from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import gradio as gr

from app.config import AppConfig, load_config
from app.history import HistoryCleanupResult, cleanup_expired_history
from app.inference import InferenceError, UpscaleResult, persist_upload, run_upscale
from app.model_registry import ResolvedModel, list_available_models
from app.request_logging import build_request_id, log_event, read_request_log_excerpt
from app.tasks import (
    TaskRecord,
    build_batch_id,
    claim_queued_task,
    create_batch,
    delete_task,
    enqueue_task,
    get_task,
    initialize_task_store,
    list_tasks,
    mark_task_completed,
    mark_task_failed,
    mark_running_tasks_interrupted,
)


Service = Callable[..., UpscaleResult]


TASK_STATUS_LABELS = {
    "queued": "排队中",
    "running": "处理中",
    "completed": "已完成",
    "failed": "失败",
    "deleted": "已删除",
    "interrupted": "已中断",
}


@dataclass(frozen=True)
class BatchRunReport:
    batch_id: str
    tasks: tuple[TaskRecord, ...]


def format_status(result: UpscaleResult) -> str:
    return (
        f"请求编号：{result.request_id}\n"
        f"模型：{result.model_name}\n"
        f"输入尺寸：{result.input_size[0]}x{result.input_size[1]}\n"
        f"输出尺寸：{result.output_size[0]}x{result.output_size[1]}\n"
        f"耗时：{result.elapsed_seconds:.2f} 秒\n"
        f"输出文件：{result.output_path}"
    )


def _model_choices(models: Sequence[ResolvedModel]) -> list[tuple[str, str]]:
    return [
        (f"{model.display_name_zh or model.display_name} ({model.display_name})", model.id)
        for model in models
    ]


def format_model_guidance(model_id: str | None, models: Sequence[ResolvedModel]) -> str:
    if not models:
        return (
            "### 模型说明\n"
            "当前没有检测到已安装模型。请把模型文件放到 `models/` 目录后重启应用。"
        )
    if not model_id:
        return "### 模型说明\n请选择一个模型后查看建议。"

    selected = next((model for model in models if model.id == model_id), None)
    if selected is None:
        return "### 模型说明\n当前选择的模型不可用，请重新选择。"

    return (
        f"### 模型说明\n"
        f"**{selected.display_name_zh or selected.display_name}**\n\n"
        f"- 适合：{selected.recommended_for_zh or '请参考模型名称选择。'}\n"
        f"- 风格：{selected.style_zh or '未标注'}\n"
        f"- 速度：{selected.speed_zh or '未标注'}\n"
        f"- 状态：{selected.stability_zh or '未标注'}\n"
        f"- 提醒：{selected.warning_zh or '当前没有额外提醒。'}"
    )


def format_error_message(error: InferenceError) -> str:
    parts = [
        f"请求编号：{error.request_id or '未生成'}",
        f"错误代码：{error.code}",
        f"错误说明：{error.user_message_zh}",
        f"可能原因：{error.likely_cause_zh}",
        f"建议操作：{error.suggested_action_zh}",
    ]
    return "\n".join(parts)


def format_progress_message(step: str, progress: float) -> str:
    percent = int(progress * 100)
    return f"当前进度：{percent}%\n阶段：{step}"


def _task_status_label(status: str) -> str:
    return TASK_STATUS_LABELS.get(status, status)


def _task_time(task: TaskRecord) -> str:
    timestamp = task.completed_at or task.started_at or task.created_at
    return timestamp.astimezone().strftime("%m-%d %H:%M")


def _task_caption(task: TaskRecord) -> str:
    source = task.input_filename or "未知输入"
    return f"{_task_time(task)} | {source} | {_task_status_label(task.status)}"


def _task_gallery(tasks: Sequence[TaskRecord]) -> list[tuple[str, str]]:
    return [
        (str(task.output_path), _task_caption(task))
        for task in tasks
        if task.status == "completed"
        and task.output_path is not None
        and task.output_path.is_file()
    ]


def _task_state(tasks: Sequence[TaskRecord]) -> list[dict[str, str]]:
    return [
        {
            "request_id": task.request_id,
            "batch_id": task.batch_id,
            "status": task.status,
            "input_filename": task.input_filename,
            "input_path": str(task.input_path),
            "output_path": str(task.output_path) if task.output_path else "",
            "model_id": task.model_id,
            "elapsed_seconds": (
                f"{task.elapsed_seconds:.2f}" if task.elapsed_seconds is not None else ""
            ),
            "created_at": task.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "started_at": (
                task.started_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                if task.started_at
                else ""
            ),
            "completed_at": (
                task.completed_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
                if task.completed_at
                else ""
            ),
            "error_code": task.error_code,
            "error_detail": task.error_detail,
        }
        for task in tasks
    ]


def _task_choices(tasks: Sequence[TaskRecord]) -> list[tuple[str, str]]:
    return [
        (
            f"{_task_status_label(task.status)} | {_task_time(task)} | "
            f"{task.input_filename or '未知输入'} | {task.request_id}",
            task.request_id,
        )
        for task in tasks
    ]


def _task_list_text(tasks: Sequence[TaskRecord]) -> str:
    if not tasks:
        return "暂无任务。提交图片后会在这里显示排队、处理中、完成和失败状态。"

    lines = []
    for task in tasks:
        elapsed = (
            f"{task.elapsed_seconds:.2f}s" if task.elapsed_seconds is not None else "-"
        )
        error = f" | {task.error_code}" if task.error_code else ""
        lines.append(
            f"{_task_status_label(task.status)} | {_task_time(task)} | "
            f"{task.input_filename or '未知输入'} | {task.model_id} | "
            f"{elapsed} | {task.request_id}{error}"
        )
    return "\n".join(lines)


def _task_summary(
    tasks: Sequence[TaskRecord],
    cleanup_result: HistoryCleanupResult | None,
    config: AppConfig,
) -> str:
    counts = {status: 0 for status in TASK_STATUS_LABELS}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1
    cleanup_text = "自动清理：关闭。"
    if config.history_retention_days > 0:
        deleted_count = len(cleanup_result.deleted_paths) if cleanup_result else 0
        cleanup_text = (
            f"自动清理：保留最近 {config.history_retention_days} 天；"
            f"本次清理 {deleted_count} 个文件。"
        )
    status_text = "，".join(
        f"{label}{counts.get(status, 0)}"
        for status, label in TASK_STATUS_LABELS.items()
    )
    return f"任务：{len(tasks)} 条（{status_text}）。{cleanup_text}"


def _task_detail(task: TaskRecord) -> str:
    elapsed = f"{task.elapsed_seconds:.2f}" if task.elapsed_seconds is not None else "未知"
    output_path = str(task.output_path) if task.output_path else "无输出文件"
    error_text = "无"
    if task.error_code:
        error_text = f"{task.error_code} | {task.error_detail or '无详细信息'}"
    return (
        f"任务编号：{task.request_id}\n"
        f"批次编号：{task.batch_id}\n"
        f"状态：{_task_status_label(task.status)}\n"
        f"创建时间：{task.created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"输入文件：{task.input_filename or '未知'}\n"
        f"输入路径：{task.input_path}\n"
        f"输出路径：{output_path}\n"
        f"模型：{task.model_id or '未知'}\n"
        f"耗时：{elapsed} 秒\n"
        f"错误：{error_text}\n"
        "提示：删除所选任务会删除这条任务对应的本地输入图和输出图。"
    )


def _task_preview_path(task: TaskRecord) -> str | None:
    if task.status != "completed" or task.output_path is None:
        return None
    if not task.output_path.is_file():
        return None
    return str(task.output_path)


def _ui_error(
    *,
    config: AppConfig,
    request_id: str,
    code: str,
    user_message_zh: str,
    likely_cause_zh: str,
    suggested_action_zh: str,
    model_id: str = "",
    input_filename: str = "",
    detail: str = "",
) -> tuple[str | None, str | None, str]:
    log_event(
        config,
        request_id=request_id,
        event="ui_rejected",
        status="failure",
        model_id=model_id,
        input_filename=input_filename,
        error_code=code,
        error_detail=detail or user_message_zh,
    )
    return (
        None,
        None,
        format_error_message(
            InferenceError(
                code=code,
                user_message_zh=user_message_zh,
                likely_cause_zh=likely_cause_zh,
                suggested_action_zh=suggested_action_zh,
                detail=detail or user_message_zh,
                request_id=request_id,
            )
        ),
    )


def _ui_error_with_log(
    *,
    config: AppConfig,
    request_id: str,
    code: str,
    user_message_zh: str,
    likely_cause_zh: str,
    suggested_action_zh: str,
    model_id: str = "",
    input_filename: str = "",
    detail: str = "",
) -> tuple[str | None, str | None, str, str]:
    preview, download, status = _ui_error(
        config=config,
        request_id=request_id,
        code=code,
        user_message_zh=user_message_zh,
        likely_cause_zh=likely_cause_zh,
        suggested_action_zh=suggested_action_zh,
        model_id=model_id,
        input_filename=input_filename,
        detail=detail,
    )
    return preview, download, status, read_request_log_excerpt(config, request_id)


def handle_upscale(
    image_path: str | None,
    model_id: str,
    output_format: str,
    quality: int,
    config: AppConfig,
    models: Sequence[ResolvedModel],
    service: Service = run_upscale,
    progress: gr.Progress | None = None,
) -> tuple[str | None, str | None, str, str]:
    request_id = build_request_id()
    queued_request_id: str | None = None
    if progress is None:
        progress = gr.Progress()
    progress(0.01, desc="请求已创建")

    def push_progress(step: str, value: float) -> None:
        progress(value, desc=step)

    if not image_path:
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="NO_IMAGE_SELECTED",
            user_message_zh="请先上传图片再开始放大。",
            likely_cause_zh="当前还没有选择任何输入图片。",
            suggested_action_zh="点击上传区域，选择一张 PNG、JPG 或 WEBP 图片后重试。",
        )

    try:
        selected = next(model for model in models if model.id == model_id)
        if not selected.absolute_path.is_file():
            return _ui_error_with_log(
                config=config,
                request_id=request_id,
                code="MODEL_FILE_MISSING",
                user_message_zh="当前模型文件不存在，无法开始放大。",
                likely_cause_zh="模型文件可能尚未放入 `models/` 目录，或文件名不匹配。",
                suggested_action_zh="请确认模型文件已放到 `models/` 目录，并与 README 要求的文件名一致。",
                model_id=model_id,
                input_filename=Path(image_path).name,
                detail=f"Model file is missing for {selected.display_name}: {selected.absolute_path}",
            )
        batch_id = build_batch_id()
        stored_input = persist_upload(
            Path(image_path),
            config,
            Path(image_path).name,
        )
        create_batch(
            config,
            batch_id=batch_id,
            model_id=model_id,
            output_format=output_format,
            quality=int(quality),
            total_count=1,
        )
        queued_task = enqueue_task(
            config,
            request_id=request_id,
            batch_id=batch_id,
            input_filename=Path(image_path).name,
            input_path=stored_input,
            model_id=model_id,
            output_format=output_format,
            quality=int(quality),
        )
        queued_request_id = queued_task.request_id
        claimed_task = claim_queued_task(config, queued_task.request_id)
        if claimed_task is None:
            raise RuntimeError("No queued task was available after enqueue.")

        progress(0.05, desc="准备校验输入与模型")
        result = service(
            image_path=claimed_task.input_path,
            original_name=claimed_task.input_filename,
            model=selected,
            config=config,
            output_format=claimed_task.output_format,
            quality=claimed_task.quality,
            request_id=claimed_task.request_id,
            progress_callback=push_progress,
            pre_persisted_input=True,
            keep_input_on_failure=True,
        )
        mark_task_completed(
            config,
            request_id=result.request_id,
            output_path=result.output_path,
            elapsed_seconds=result.elapsed_seconds,
        )
    except StopIteration:
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="MODEL_NOT_AVAILABLE",
            user_message_zh="当前选择的模型不可用。",
            likely_cause_zh="模型列表已变化，或当前模型没有成功加载到界面中。",
            suggested_action_zh="请重新选择模型；如果列表为空，请先确认 `models/` 目录里已有可用模型。",
            model_id=model_id,
            input_filename=Path(image_path).name,
            detail=f"selected model is not available: {model_id}",
        )
    except InferenceError as exc:
        exc.request_id = exc.request_id or request_id
        if queued_request_id is not None:
            mark_task_failed(
                config,
                request_id=queued_request_id,
                error_code=exc.code,
                error_detail=exc.detail,
            )
        request_log = read_request_log_excerpt(config, exc.request_id)
        if request_log == "当前请求还没有日志片段。":
            request_log = f"[failure] ui_error | error_code={exc.code} | detail={exc.detail}"
        return None, None, format_error_message(exc), request_log
    except ValueError as exc:
        if queued_request_id is not None:
            mark_task_failed(
                config,
                request_id=queued_request_id,
                error_code="INVALID_REQUEST",
                error_detail=str(exc),
            )
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="INVALID_REQUEST",
            user_message_zh="请求参数无效，无法开始放大。",
            likely_cause_zh="输出格式或质量参数超出当前允许范围。",
            suggested_action_zh="请恢复默认参数后重试。",
            model_id=model_id,
            input_filename=Path(image_path).name,
            detail=str(exc),
        )
    except Exception as exc:
        if queued_request_id is not None:
            mark_task_failed(
                config,
                request_id=queued_request_id,
                error_code="UNEXPECTED_UI_FAILURE",
                error_detail=str(exc),
            )
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="UNEXPECTED_UI_FAILURE",
            user_message_zh="界面处理过程中发生未预期错误。",
            likely_cause_zh="当前请求没有被应用正常接住，可能需要查看日志排查。",
            suggested_action_zh="请重试一次；如果仍失败，请提供请求编号并查看 `logs/` 下的日志。",
            model_id=model_id,
            input_filename=Path(image_path).name,
            detail=str(exc),
        )

    request_log = read_request_log_excerpt(config, result.request_id)
    if request_log == "当前请求还没有日志片段。":
        request_log = "[success] request_succeeded"
    return (
        str(result.output_path),
        str(result.output_path),
        format_status(result),
        request_log,
    )


def _coerce_upload_paths(image_paths: object) -> list[Path]:
    if image_paths is None:
        return []
    if isinstance(image_paths, (str, Path)):
        return [Path(image_paths)]
    if isinstance(image_paths, Sequence):
        return [Path(path) for path in image_paths if path]
    return []


def _task_progress(
    progress: gr.Progress,
    *,
    index: int,
    total: int,
) -> Callable[[str, float], None]:
    def push(step: str, value: float) -> None:
        progress((index + value) / max(total, 1), desc=f"{index + 1}/{total} {step}")

    return push


def _process_queued_task(
    *,
    config: AppConfig,
    task: TaskRecord,
    selected: ResolvedModel,
    service: Service,
    progress_callback: Callable[[str, float], None],
) -> TaskRecord:
    claimed_task = claim_queued_task(config, task.request_id)
    if claimed_task is None:
        return mark_task_failed(
            config,
            request_id=task.request_id,
            error_code="TASK_CLAIM_FAILED",
            error_detail="Queued task could not be claimed for processing.",
        )

    try:
        result = service(
            image_path=claimed_task.input_path,
            original_name=claimed_task.input_filename,
            model=selected,
            config=config,
            output_format=claimed_task.output_format,
            quality=claimed_task.quality,
            request_id=claimed_task.request_id,
            progress_callback=progress_callback,
            pre_persisted_input=True,
            keep_input_on_failure=True,
        )
    except InferenceError as exc:
        exc.request_id = exc.request_id or claimed_task.request_id
        return mark_task_failed(
            config,
            request_id=claimed_task.request_id,
            error_code=exc.code,
            error_detail=exc.detail,
        )
    except ValueError as exc:
        return mark_task_failed(
            config,
            request_id=claimed_task.request_id,
            error_code="INVALID_REQUEST",
            error_detail=str(exc),
        )
    except Exception as exc:
        return mark_task_failed(
            config,
            request_id=claimed_task.request_id,
            error_code="UNEXPECTED_UI_FAILURE",
            error_detail=str(exc),
        )

    return mark_task_completed(
        config,
        request_id=claimed_task.request_id,
        output_path=result.output_path,
        elapsed_seconds=result.elapsed_seconds,
    )


def format_batch_status(report: BatchRunReport) -> str:
    completed = [task for task in report.tasks if task.status == "completed"]
    failed = [task for task in report.tasks if task.status == "failed"]
    interrupted = [task for task in report.tasks if task.status == "interrupted"]
    lines = [
        f"批次编号：{report.batch_id}",
        f"总数：{len(report.tasks)}",
        f"已完成：{len(completed)}",
        f"失败：{len(failed)}",
        f"已中断：{len(interrupted)}",
        "处理方式：CPU 顺序处理，不会并行加速。",
    ]
    first_completed = next((task for task in completed if task.output_path), None)
    if first_completed is not None:
        lines.append(f"首个输出：{first_completed.output_path}")
    if failed:
        lines.append("失败任务：")
        lines.extend(
            f"- {task.request_id} | {task.input_filename} | {task.error_code}"
            for task in failed
        )
    return "\n".join(lines)


def _batch_log_excerpt(config: AppConfig, tasks: Sequence[TaskRecord]) -> str:
    if not tasks:
        return "当前批次没有可显示的任务日志。"
    sections = []
    for task in tasks[:5]:
        sections.append(
            f"--- {task.request_id} | {_task_status_label(task.status)} ---\n"
            f"{read_request_log_excerpt(config, task.request_id)}"
        )
    if len(tasks) > 5:
        sections.append(f"还有 {len(tasks) - 5} 个任务，请在任务列表中选择查看。")
    return "\n".join(sections)


def handle_batch_upscale(
    image_paths: object,
    model_id: str,
    output_format: str,
    quality: int,
    config: AppConfig,
    models: Sequence[ResolvedModel],
    service: Service = run_upscale,
    progress: gr.Progress | None = None,
) -> tuple[str | None, str | None, str, str]:
    request_id = build_request_id()
    paths = _coerce_upload_paths(image_paths)
    if progress is None:
        progress = gr.Progress()
    progress(0.01, desc="请求已创建")

    if not paths:
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="NO_IMAGE_SELECTED",
            user_message_zh="请先上传图片再开始放大。",
            likely_cause_zh="当前还没有选择任何输入图片。",
            suggested_action_zh="点击上传区域，选择一张或多张 PNG、JPG 或 WEBP 图片后重试。",
        )

    try:
        selected = next(model for model in models if model.id == model_id)
    except StopIteration:
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="MODEL_NOT_AVAILABLE",
            user_message_zh="当前选择的模型不可用。",
            likely_cause_zh="模型列表已变化，或当前模型没有成功加载到界面中。",
            suggested_action_zh="请重新选择模型；如果列表为空，请先确认 `models/` 目录里已有可用模型。",
            model_id=model_id,
            input_filename=paths[0].name,
            detail=f"selected model is not available: {model_id}",
        )
    if not selected.absolute_path.is_file():
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="MODEL_FILE_MISSING",
            user_message_zh="当前模型文件不存在，无法开始放大。",
            likely_cause_zh="模型文件可能尚未放入 `models/` 目录，或文件名不匹配。",
            suggested_action_zh="请确认模型文件已放到 `models/` 目录，并与 README 要求的文件名一致。",
            model_id=model_id,
            input_filename=paths[0].name,
            detail=f"Model file is missing for {selected.display_name}: {selected.absolute_path}",
        )

    batch_id = build_batch_id()
    create_batch(
        config,
        batch_id=batch_id,
        model_id=model_id,
        output_format=output_format,
        quality=int(quality),
        total_count=len(paths),
    )

    queued_tasks: list[TaskRecord] = []
    for path in paths:
        task_request_id = build_request_id()
        stored_input = persist_upload(path, config, path.name)
        queued_tasks.append(
            enqueue_task(
                config,
                request_id=task_request_id,
                batch_id=batch_id,
                input_filename=path.name,
                input_path=stored_input,
                model_id=model_id,
                output_format=output_format,
                quality=int(quality),
            )
        )

    processed_tasks = [
        _process_queued_task(
            config=config,
            task=task,
            selected=selected,
            service=service,
            progress_callback=_task_progress(
                progress,
                index=index,
                total=len(queued_tasks),
            ),
        )
        for index, task in enumerate(queued_tasks)
    ]
    progress(1.0, desc="批次处理完成")

    report = BatchRunReport(batch_id=batch_id, tasks=tuple(processed_tasks))
    preview_task = next(
        (
            task
            for task in processed_tasks
            if task.status == "completed"
            and task.output_path is not None
            and task.output_path.is_file()
        ),
        None,
    )
    preview_path = str(preview_task.output_path) if preview_task else None
    return (
        preview_path,
        preview_path,
        format_batch_status(report),
        _batch_log_excerpt(config, processed_tasks),
    )


def build_demo(config: AppConfig | None = None) -> gr.Blocks:
    runtime_config = config or load_config()
    runtime_config.ensure_directories()
    initialize_task_store(runtime_config)
    mark_running_tasks_interrupted(runtime_config)
    initial_cleanup = cleanup_expired_history(runtime_config)
    models = list_available_models(runtime_config.models_dir)
    choices = _model_choices(models)
    default_model = choices[0][1] if choices else None
    initial_status = "请上传图片，选择模型后开始放大。"
    if not choices:
        initial_status = (
            "当前没有检测到已安装模型。请把模型文件放到 models 目录后重启应用。"
        )
    initial_guidance = format_model_guidance(default_model, models)
    initial_logs = "当前还没有本次请求日志。开始处理后，这里会显示该请求的关键日志片段。"
    initial_tasks = list_tasks(runtime_config, limit=runtime_config.history_limit)
    initial_task_gallery = _task_gallery(initial_tasks)
    initial_task_state = _task_state(initial_tasks)
    initial_task_choices = _task_choices(initial_tasks)
    initial_task_list = _task_list_text(initial_tasks)
    initial_task_status = _task_summary(initial_tasks, initial_cleanup, runtime_config)

    def task_values() -> tuple[
        list[tuple[str, str]],
        list[dict[str, str]],
        str,
        object,
        str,
    ]:
        cleanup_result = cleanup_expired_history(runtime_config)
        tasks = list_tasks(runtime_config, limit=runtime_config.history_limit)
        choices = _task_choices(tasks)
        return (
            _task_gallery(tasks),
            _task_state(tasks),
            _task_list_text(tasks),
            gr.update(choices=choices, value=None, interactive=bool(choices)),
            _task_summary(tasks, cleanup_result, runtime_config),
        )

    def on_submit(
        image_paths: object,
        model_id: str,
        output_format: str,
        quality: int,
        progress: gr.Progress = gr.Progress(),
    ) -> tuple[
        str | None,
        str | None,
        str,
        str,
        list[tuple[str, str]],
        list[dict[str, str]],
        str,
        object,
        str,
        str,
    ]:
        preview, download, status_text, request_log = handle_batch_upscale(
            image_paths=image_paths,
            model_id=model_id,
            output_format=output_format,
            quality=quality,
            config=runtime_config,
            models=models,
            progress=progress,
        )
        gallery, state, task_list_text, choices_update, task_status = task_values()
        return (
            preview,
            download,
            status_text,
            request_log,
            gallery,
            state,
            task_list_text,
            choices_update,
            "",
            task_status,
        )

    def on_model_change(model_id: str) -> str:
        return format_model_guidance(model_id, models)

    def on_task_refresh() -> tuple[
        list[tuple[str, str]],
        list[dict[str, str]],
        str,
        object,
        str,
        str,
    ]:
        gallery, state, task_list_text, choices_update, task_status = task_values()
        return gallery, state, task_list_text, choices_update, "", task_status

    def on_task_select(
        request_id: str | None,
    ) -> tuple[str, str | None, str | None, str, str]:
        if not request_id:
            return "", None, None, "请选择一条任务。", "当前没有选中的任务日志。"
        task = get_task(runtime_config, request_id)
        if task is None:
            return "", None, None, "没有找到这条任务。", "当前任务没有日志片段。"
        preview_path = _task_preview_path(task)
        return (
            request_id,
            preview_path,
            preview_path,
            _task_detail(task),
            read_request_log_excerpt(runtime_config, request_id),
        )

    def on_task_delete(
        selected_request_id: str,
    ) -> tuple[
        list[tuple[str, str]],
        list[dict[str, str]],
        str,
        object,
        str,
        str | None,
        str | None,
        str,
        str,
        str,
    ]:
        if not selected_request_id:
            gallery, state, task_list_text, choices_update, task_status = task_values()
            return (
                gallery,
                state,
                task_list_text,
                choices_update,
                "",
                None,
                None,
                "请先在任务列表里选择要删除的任务。",
                "当前没有选中的任务日志。",
                task_status,
            )
        result = delete_task(runtime_config, selected_request_id)
        request_log = read_request_log_excerpt(runtime_config, selected_request_id)
        gallery, state, task_list_text, choices_update, task_status = task_values()
        return (
            gallery,
            state,
            task_list_text,
            choices_update,
            "",
            None,
            None,
            result.message_zh,
            request_log,
            task_status,
        )

    with gr.Blocks(title="Pixloom") as demo:
        gr.Markdown("# Pixloom 图片放大")
        gr.Markdown("适合 NAS 的 CPU 单张或批量图片超分工具。批量任务会按顺序处理。")
        selected_task_id = gr.State("")
        task_state = gr.State(initial_task_state)
        with gr.Row():
            with gr.Column():
                image_input = gr.File(
                    label="上传图片（可多选）",
                    file_count="multiple",
                    file_types=[".png", ".jpg", ".jpeg", ".webp"],
                    type="filepath",
                )
                model_input = gr.Dropdown(
                    label="模型",
                    choices=choices,
                    value=default_model,
                    interactive=bool(choices),
                )
                model_guidance = gr.Markdown(value=initial_guidance)
                output_format = gr.Radio(
                    label="输出格式",
                    choices=["PNG", "JPG", "WEBP"],
                    value="PNG",
                )
                quality = gr.Slider(
                    label="JPG / WEBP 质量",
                    minimum=1,
                    maximum=100,
                    value=90,
                    step=1,
                )
                submit = gr.Button("提交任务", variant="primary", interactive=bool(choices))
            with gr.Column():
                preview = gr.Image(label="结果预览", type="filepath")
                download = gr.File(label="下载文件")
                status = gr.Textbox(label="状态与提示", lines=8, value=initial_status)
                request_logs = gr.Textbox(label="本次请求日志", lines=10, value=initial_logs)
                gr.Markdown("### 任务列表")
                task_selector = gr.Dropdown(
                    label="选择任务",
                    choices=initial_task_choices,
                    value=None,
                    interactive=bool(initial_task_choices),
                )
                task_list = gr.Textbox(
                    label="最近任务",
                    lines=12,
                    value=initial_task_list,
                )
                task_gallery = gr.Gallery(
                    label="已完成图片",
                    value=initial_task_gallery,
                    columns=3,
                    height=260,
                    allow_preview=True,
                )
                with gr.Row():
                    refresh_tasks = gr.Button("刷新任务")
                    delete_selected_task = gr.Button("删除所选任务", variant="stop")
                task_status = gr.Textbox(
                    label="任务状态",
                    lines=3,
                    value=initial_task_status,
                )

        if choices:
            model_input.change(
                fn=on_model_change,
                inputs=[model_input],
                outputs=[model_guidance],
            )
            submit.click(
                fn=on_submit,
                inputs=[image_input, model_input, output_format, quality],
                outputs=[
                    preview,
                    download,
                    status,
                    request_logs,
                    task_gallery,
                    task_state,
                    task_list,
                    task_selector,
                    selected_task_id,
                    task_status,
                ],
            )
        task_selector.change(
            fn=on_task_select,
            inputs=[task_selector],
            outputs=[
                selected_task_id,
                preview,
                download,
                status,
                request_logs,
            ],
        )
        refresh_tasks.click(
            fn=on_task_refresh,
            outputs=[
                task_gallery,
                task_state,
                task_list,
                task_selector,
                selected_task_id,
                task_status,
            ],
        )
        delete_selected_task.click(
            fn=on_task_delete,
            inputs=[selected_task_id],
            outputs=[
                task_gallery,
                task_state,
                task_list,
                task_selector,
                selected_task_id,
                preview,
                download,
                status,
                request_logs,
                task_status,
            ],
        )

    return demo


def main() -> None:
    config = load_config()
    demo = build_demo(config)
    demo.queue(default_concurrency_limit=1).launch(
        server_name=config.server_name,
        server_port=config.server_port,
        auth=config.gradio_auth,
        allowed_paths=[
            str(config.output_dir.resolve()),
            str(config.input_dir.resolve()),
        ],
    )


if __name__ == "__main__":
    main()
