from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Lock, Thread
import time

import gradio as gr

from app.config import AppConfig, load_config
from app.history import HistoryCleanupResult, cleanup_expired_history
from app.inference import InferenceError, UpscaleResult, persist_upload, run_upscale
from app.model_registry import (
    ModelNotFoundError,
    ResolvedModel,
    list_available_models,
    list_installed_models,
    resolve_model,
)
from app.request_logging import build_request_id, log_event, read_request_log_excerpt
from app.tasks import (
    QueuedTaskInput,
    TaskRecord,
    build_batch_id,
    claim_next_queued_task,
    claim_queued_task,
    create_batch_with_tasks,
    delete_task,
    get_task,
    initialize_task_store,
    list_tasks,
    mark_task_completed,
    mark_task_failed,
    mark_running_tasks_interrupted,
    update_task_progress,
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


APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --pix-bg: #eef2f7;
    --pix-surface: rgba(255, 255, 255, 0.9);
    --pix-surface-strong: #f8fafc;
    --pix-ink: #0f172a;
    --pix-muted: #475569;
    --pix-line: #cbd5e1;
    --pix-accent: #1d7a5a;
    --pix-accent-strong: #14532d;
    --pix-danger: #b91c1c;
    --pix-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}

body,
.gradio-container,
input,
textarea,
select,
button {
    font-family: "Fira Sans", sans-serif !important;
}

code,
pre {
    font-family: "Fira Code", monospace !important;
}

body {
    background: linear-gradient(180deg, #e8eef4 0%, #f8fafc 34%, #eef2f7 100%) fixed;
}

.gradio-container {
    max-width: 1380px !important;
    margin: 0 auto !important;
    padding: 20px 14px 36px !important;
    background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.5)),
        repeating-linear-gradient(
            90deg,
            rgba(148, 163, 184, 0.08) 0 1px,
            transparent 1px 24px
        ),
        repeating-linear-gradient(
            0deg,
            rgba(148, 163, 184, 0.06) 0 1px,
            transparent 1px 24px
        );
}

#pix-shell-header {
    margin-bottom: 16px;
    padding: 22px 22px 18px;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 8px;
    color: #f8fafc;
    background: linear-gradient(135deg, #0f172a 0%, #16263b 54%, #0a1220 100%);
    box-shadow: 0 24px 60px rgba(15, 23, 42, 0.18);
}

#pix-shell-header .pix-title-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: flex-end;
    gap: 16px;
}

#pix-shell-header .pix-shell-label {
    margin: 0 0 8px;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
    font-family: "Fira Code", monospace;
}

#pix-shell-header .pix-shell-title {
    margin: 0;
    font-size: clamp(1.8rem, 3vw, 2.8rem);
    line-height: 1.05;
    font-weight: 700;
    font-family: "Fira Code", monospace;
    letter-spacing: 0;
}

#pix-shell-header .pix-shell-copy {
    margin: 6px 0 0;
    max-width: 50rem;
    font-size: 0.96rem;
    line-height: 1.6;
    color: #cbd5e1;
}

#pix-shell-header .pix-shell-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    min-width: min(100%, 430px);
}

#pix-shell-header .pix-metric {
    padding: 12px 14px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.28);
}

#pix-shell-header .pix-metric-value {
    display: block;
    font-size: 1.2rem;
    font-weight: 600;
    color: #f8fafc;
    font-family: "Fira Code", monospace;
}

#pix-shell-header .pix-metric-label {
    display: block;
    margin-top: 4px;
    font-size: 12px;
    color: #94a3b8;
}

.pix-main-grid {
    align-items: stretch !important;
    gap: 16px !important;
}

.pix-panel {
    padding: 18px;
    border: 1px solid var(--pix-line);
    border-radius: 8px;
    background: var(--pix-surface);
    box-shadow: var(--pix-shadow);
    backdrop-filter: blur(12px);
}

.pix-panel-head {
    margin: 0 0 12px;
}

.pix-panel-head .pix-eyebrow {
    margin: 0 0 4px;
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--pix-accent);
    font-family: "Fira Code", monospace;
}

.pix-panel-head .pix-section-title {
    margin: 0;
    font-size: 1.05rem;
    line-height: 1.3;
    font-weight: 600;
    color: var(--pix-ink);
}

.pix-panel-head .pix-section-copy {
    margin: 4px 0 0;
    font-size: 0.92rem;
    line-height: 1.55;
    color: var(--pix-muted);
}

#pix-upload,
#pix-model-picker,
#pix-format,
#pix-quality,
#pix-guidance,
#pix-preview,
#pix-download,
#pix-status,
#pix-live-status,
#pix-task-summary,
#pix-task-picker,
#pix-task-detail,
#pix-task-list,
#pix-gallery,
#pix-logs {
    border-radius: 8px;
}

#pix-guidance {
    margin-top: 10px;
    padding: 14px 16px;
    border: 1px solid #d5e4db;
    background: linear-gradient(180deg, #fcfffd 0%, #f3f8f5 100%);
}

#pix-guidance h3 {
    margin: 0 0 10px;
    font-size: 0.95rem;
    font-family: "Fira Code", monospace;
}

#pix-guidance p,
#pix-guidance li,
#pix-guidance strong {
    color: var(--pix-ink);
}

#pix-guidance ul {
    margin: 0;
    padding-left: 20px;
}

#pix-submit-button button,
#pix-refresh-button button,
#pix-delete-button button {
    min-height: 46px;
    border-radius: 8px;
    font-weight: 600;
    transition:
        transform 180ms ease,
        background-color 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease;
}

#pix-submit-button button:hover,
#pix-refresh-button button:hover,
#pix-delete-button button:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 20px rgba(15, 23, 42, 0.12);
}

#pix-refresh-button button {
    color: #1d4ed8;
    border-color: #bfdbfe;
    background: #eff6ff;
}

#pix-delete-button button {
    color: var(--pix-danger);
    border-color: #fecaca;
    background: #fff7f7;
}

#pix-results-tabs .tab-nav {
    padding-bottom: 8px;
    border-bottom: 1px solid var(--pix-line);
    background: transparent;
}

#pix-results-tabs .tab-nav button {
    min-height: 40px;
    border-radius: 999px;
    font-weight: 600;
}

#pix-results-tabs .tab-nav button.selected {
    color: #f8fafc;
    background: var(--pix-ink);
}

#pix-status textarea,
#pix-live-status textarea,
#pix-task-summary textarea,
#pix-task-detail textarea,
#pix-task-list textarea,
#pix-logs textarea {
    color: var(--pix-ink) !important;
    line-height: 1.55 !important;
    border: 1px solid #d8e1ea !important;
    background: var(--pix-surface-strong) !important;
    box-shadow: none !important;
}

#pix-task-summary textarea {
    font-weight: 500;
}

#pix-task-detail textarea,
#pix-logs textarea {
    font-size: 0.85rem !important;
    font-family: "Fira Code", monospace !important;
}

#pix-preview {
    padding: 10px;
    border: 1px solid #d7e3eb;
    background: linear-gradient(180deg, #fbfdff, #eef4f8);
}

#pix-task-accordion,
#pix-gallery-accordion,
#pix-model-accordion,
#pix-output-accordion {
    border: 1px solid #d7dee8 !important;
    border-radius: 8px !important;
    background: #fbfcfe !important;
}

#pix-task-accordion .label-wrap,
#pix-gallery-accordion .label-wrap,
#pix-model-accordion .label-wrap,
#pix-output-accordion .label-wrap {
    font-weight: 600;
    color: var(--pix-ink);
}

#pix-model-picker label,
#pix-upload label,
#pix-format label,
#pix-quality label,
#pix-preview label,
#pix-download label,
#pix-status label,
#pix-task-summary label,
#pix-task-picker label,
#pix-task-detail label,
#pix-task-list label,
#pix-logs label {
    color: var(--pix-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}

@media (max-width: 900px) {
    .gradio-container {
        padding: 14px 10px 30px !important;
    }

    #pix-shell-header {
        padding: 18px 16px;
    }

    #pix-shell-header .pix-title-row {
        align-items: flex-start;
    }

    #pix-shell-header .pix-shell-metrics {
        min-width: 100%;
        grid-template-columns: 1fr;
    }

    .pix-panel {
        padding: 14px;
    }

    #pix-task-detail textarea,
    #pix-logs textarea {
        min-height: 220px;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
"""


@dataclass(frozen=True)
class BatchTaskReport:
    batch_id: str
    tasks: tuple[TaskRecord, ...]


class BackgroundTaskWorker:
    def __init__(
        self,
        *,
        config: AppConfig,
        service: Service = run_upscale,
        poll_interval_seconds: float = 1.0,
    ) -> None:
        self._config = config
        self._service = service
        self._poll_interval_seconds = poll_interval_seconds
        self._stop_event = Event()
        self._thread = Thread(
            target=self._run_loop,
            name=f"pixloom-worker-{config.db_path.stem}",
            daemon=True,
        )

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def is_alive(self) -> bool:
        return self._thread.is_alive()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            processed = process_next_queued_task(self._config, service=self._service)
            if processed is not None:
                continue
            self._stop_event.wait(self._poll_interval_seconds)


_WORKERS: dict[str, BackgroundTaskWorker] = {}
_WORKERS_LOCK = Lock()


def format_status(result: UpscaleResult) -> str:
    return (
        f"请求编号：{result.request_id}\n"
        f"模型：{result.model_name}\n"
        f"输入尺寸：{result.input_size[0]}x{result.input_size[1]}\n"
        f"输出尺寸：{result.output_size[0]}x{result.output_size[1]}\n"
        f"耗时：{result.elapsed_seconds:.2f} 秒\n"
        f"输出文件：{result.output_path}"
    )


def _shell_header_html(
    *,
    operator_count: int,
    installed_count: int,
    hidden_local_models_count: int,
) -> str:
    return (
        '<div id="pix-shell-header">'
        '<div class="pix-title-row">'
        "<div>"
        '<p class="pix-shell-label">NAS CPU Console</p>'
        '<h1 class="pix-shell-title">Pixloom</h1>'
        '<p class="pix-shell-copy">图片先落盘，再进入后台串行队列。手机端只保留最短提交路径，'
        "结果、任务和日志各自收口，避免一整列长面板把状态冲散。</p>"
        "</div>"
        '<div class="pix-shell-metrics">'
        f'<div class="pix-metric"><span class="pix-metric-value">{operator_count}</span>'
        '<span class="pix-metric-label">当前开放模型</span></div>'
        f'<div class="pix-metric"><span class="pix-metric-value">{installed_count}</span>'
        '<span class="pix-metric-label">本地模型文件</span></div>'
        f'<div class="pix-metric"><span class="pix-metric-value">{hidden_local_models_count}</span>'
        '<span class="pix-metric-label">评估池未开放</span></div>'
        "</div>"
        "</div>"
        "</div>"
    )


def _panel_head_html(eyebrow: str, title: str, copy: str) -> str:
    return (
        '<div class="pix-panel-head">'
        f'<p class="pix-eyebrow">{eyebrow}</p>'
        f'<h2 class="pix-section-title">{title}</h2>'
        f'<p class="pix-section-copy">{copy}</p>'
        "</div>"
    )


def _model_choices(models: Sequence[ResolvedModel]) -> list[tuple[str, str]]:
    return [
        (f"{model.display_name_zh or model.display_name} ({model.display_name})", model.id)
        for model in models
    ]


def format_model_guidance(
    model_id: str | None,
    models: Sequence[ResolvedModel],
    *,
    has_local_models: bool = False,
    hidden_local_models_count: int = 0,
) -> str:
    if not models:
        if has_local_models:
            hidden_text = ""
            if hidden_local_models_count > 0:
                hidden_text = f"当前有 {hidden_local_models_count} 个本地模型仍在评估中。"
            return (
                "### 模型说明\n"
                "当前本地已有模型，但还没有已验收并开放给日常操作的模型。"
                f"{hidden_text}请先完成本机验收，或调整开放状态后重启应用。"
            )
        return (
            "### 模型说明\n"
            "当前没有检测到已安装模型。请把模型文件放到 `models/` 目录后重启应用。"
        )
    if not model_id:
        return "### 模型说明\n请选择一个模型后查看建议。"

    selected = next((model for model in models if model.id == model_id), None)
    if selected is None:
        return "### 模型说明\n当前选择的模型不可用，请重新选择。"

    guidance = (
        f"### 模型说明\n"
        f"**{selected.display_name_zh or selected.display_name}**\n\n"
        f"- 适合：{selected.recommended_for_zh or '请参考模型名称选择。'}\n"
        f"- 风格：{selected.style_zh or '未标注'}\n"
        f"- 速度：{selected.speed_zh or '未标注'}\n"
        f"- 状态：{selected.stability_zh or '未标注'}\n"
        f"- 提醒：{selected.warning_zh or '当前没有额外提醒。'}"
    )
    if hidden_local_models_count > 0:
        guidance += f"\n- 说明：当前仅显示已验收模型；另有 {hidden_local_models_count} 个本地模型仍在评估中。"
    return guidance


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


def _task_elapsed_seconds(task: TaskRecord) -> float | None:
    if task.elapsed_seconds is not None:
        return task.elapsed_seconds
    if task.status == "running" and task.started_at is not None:
        return max(
            0.0,
            (datetime.now(timezone.utc) - task.started_at).total_seconds(),
        )
    return None


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "未知"
    if seconds < 60:
        return f"{seconds:.0f} 秒"
    minutes, remaining_seconds = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes} 分 {remaining_seconds} 秒"
    hours, remaining_minutes = divmod(minutes, 60)
    return f"{hours} 小时 {remaining_minutes} 分"


def _task_eta_seconds(task: TaskRecord) -> float | None:
    if task.status != "running":
        return None
    if task.progress_value <= 0 or task.progress_value >= 1:
        return None
    elapsed = _task_elapsed_seconds(task)
    if elapsed is None or elapsed <= 0:
        return None
    return max(0.0, elapsed * (1 - task.progress_value) / task.progress_value)


def _task_progress_summary(task: TaskRecord) -> str:
    if task.status == "queued":
        return "等待后台处理"
    if task.status == "running":
        percent = int(task.progress_value * 100)
        eta = _task_eta_seconds(task)
        eta_text = _format_duration(eta) if eta is not None else "计算中"
        step = task.progress_step or "处理中"
        return f"{percent}% | {step} | 预计剩余 {eta_text}"
    if task.status == "completed":
        return "100% | 处理完成"
    if task.progress_step:
        return task.progress_step
    return "-"


def _selected_task_status_text(task: TaskRecord | None) -> str:
    if task is None:
        return "请上传图片，选择模型后提交。任务会在后台顺序处理。"

    lines = [
        f"请求编号：{task.request_id}",
        f"状态：{_task_status_label(task.status)}",
        f"模型：{task.model_id}",
    ]
    if task.status in {"queued", "running"}:
        lines.append(f"当前阶段：{task.progress_step or '等待开始'}")
        lines.append(f"当前进度：{int(task.progress_value * 100)}%")
        lines.append(f"进度摘要：{_task_progress_summary(task)}")
        lines.append(f"已用时：{_format_duration(_task_elapsed_seconds(task))}")
        eta = _task_eta_seconds(task)
        lines.append(f"预计剩余：{_format_duration(eta) if eta is not None else '计算中'}")
    elif task.status == "completed":
        lines.append(f"耗时：{_format_duration(task.elapsed_seconds)}")
        lines.append(f"输出文件：{task.output_path or '无输出文件'}")
    elif task.status == "failed":
        lines.append(f"错误：{task.error_code or '未知错误'}")
        lines.append(f"最后阶段：{task.progress_step or '处理中断'}")
        lines.append("建议：切到“日志”页查看 request id 对应的详细失败记录。")
    else:
        lines.append(f"进度摘要：{_task_progress_summary(task)}")
    return "\n".join(lines)


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
            "progress_value": f"{task.progress_value:.3f}",
            "progress_step": task.progress_step,
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
        progress = _task_progress_summary(task)
        lines.append(
            f"{_task_status_label(task.status)} | {_task_time(task)} | "
            f"{task.input_filename or '未知输入'} | {task.model_id} | "
            f"{progress} | {elapsed} | {task.request_id}{error}"
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
    elapsed = _format_duration(_task_elapsed_seconds(task))
    output_path = str(task.output_path) if task.output_path else "无输出文件"
    error_text = "无"
    if task.error_code:
        error_text = f"{task.error_code} | {task.error_detail or '无详细信息'}"
    eta_text = "无"
    eta = _task_eta_seconds(task)
    if eta is not None:
        eta_text = _format_duration(eta)
    return (
        f"任务编号：{task.request_id}\n"
        f"批次编号：{task.batch_id}\n"
        f"状态：{_task_status_label(task.status)}\n"
        f"创建时间：{task.created_at.astimezone().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"输入文件：{task.input_filename or '未知'}\n"
        f"输入路径：{task.input_path}\n"
        f"输出路径：{output_path}\n"
        f"模型：{task.model_id or '未知'}\n"
        f"阶段：{task.progress_step or '无'}\n"
        f"进度：{int(task.progress_value * 100)}%\n"
        f"预计剩余：{eta_text}\n"
        f"耗时：{elapsed}\n"
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
    persisted_inputs: list[Path] = []
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
        persisted_batch = _persist_batch_inputs([Path(image_path)], config)
        persisted_inputs = [stored_input for _, stored_input in persisted_batch]
        queued_task = _queue_persisted_batch(
            config=config,
            batch_id=build_batch_id(),
            model_id=model_id,
            output_format=output_format,
            quality=int(quality),
            persisted_inputs=persisted_batch,
        )
        queued_request_id = queued_task[0].request_id
        claimed_task = claim_queued_task(config, queued_request_id)
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
        if queued_request_id is None:
            _unlink_paths(persisted_inputs)
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
        if queued_request_id is None:
            _unlink_paths(persisted_inputs)
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


def _unlink_paths(paths: Sequence[Path]) -> None:
    for path in paths:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _persist_batch_inputs(
    paths: Sequence[Path],
    config: AppConfig,
) -> list[tuple[str, Path]]:
    persisted: list[tuple[str, Path]] = []
    try:
        for path in paths:
            persisted.append((path.name, persist_upload(path, config, path.name)))
    except Exception:
        _unlink_paths([stored for _, stored in persisted])
        raise
    return persisted


def _queue_persisted_batch(
    *,
    config: AppConfig,
    batch_id: str,
    model_id: str,
    output_format: str,
    quality: int,
    persisted_inputs: Sequence[tuple[str, Path]],
) -> tuple[TaskRecord, ...]:
    task_inputs = tuple(
        QueuedTaskInput(
            request_id=build_request_id(),
            input_filename=input_filename,
            input_path=stored_input,
            model_id=model_id,
            output_format=output_format,
            quality=int(quality),
        )
        for input_filename, stored_input in persisted_inputs
    )
    return create_batch_with_tasks(
        config,
        batch_id=batch_id,
        model_id=model_id,
        output_format=output_format,
        quality=int(quality),
        tasks=task_inputs,
    )


def _task_progress(
    progress: gr.Progress,
    *,
    index: int,
    total: int,
) -> Callable[[str, float], None]:
    def push(step: str, value: float) -> None:
        progress((index + value) / max(total, 1), desc=f"{index + 1}/{total} {step}")

    return push


def _run_claimed_task(
    *,
    config: AppConfig,
    task: TaskRecord,
    service: Service,
    selected_model: ResolvedModel | None = None,
    progress_callback: Callable[[str, float], None] | None = None,
) -> TaskRecord:
    selected = selected_model
    if selected is None:
        try:
            selected = resolve_model(task.model_id, config.models_dir)
        except ModelNotFoundError as exc:
            return mark_task_failed(
                config,
                request_id=task.request_id,
                error_code="MODEL_NOT_AVAILABLE",
                error_detail=str(exc),
            )

    last_progress_value = task.progress_value
    last_progress_step = task.progress_step
    last_progress_write = time.monotonic()

    def persist_progress(step: str, value: float) -> None:
        nonlocal last_progress_value, last_progress_step, last_progress_write
        normalized = max(0.0, min(1.0, float(value)))
        now = time.monotonic()
        should_write = (
            step != last_progress_step
            or abs(normalized - last_progress_value) >= 0.03
            or normalized >= 1.0
            or (now - last_progress_write) >= 0.75
        )
        if should_write:
            update_task_progress(
                config,
                request_id=task.request_id,
                progress_value=normalized,
                progress_step=step,
            )
            last_progress_value = normalized
            last_progress_step = step
            last_progress_write = now
        if progress_callback is not None:
            progress_callback(step, normalized)

    update_task_progress(
        config,
        request_id=task.request_id,
        progress_value=max(task.progress_value, 0.05),
        progress_step="准备开始推理",
    )

    try:
        result = service(
            image_path=task.input_path,
            original_name=task.input_filename,
            model=selected,
            config=config,
            output_format=task.output_format,
            quality=task.quality,
            request_id=task.request_id,
            progress_callback=persist_progress,
            pre_persisted_input=True,
            keep_input_on_failure=True,
        )
    except InferenceError as exc:
        exc.request_id = exc.request_id or task.request_id
        return mark_task_failed(
            config,
            request_id=task.request_id,
            error_code=exc.code,
            error_detail=exc.detail,
        )
    except ValueError as exc:
        return mark_task_failed(
            config,
            request_id=task.request_id,
            error_code="INVALID_REQUEST",
            error_detail=str(exc),
        )
    except Exception as exc:
        return mark_task_failed(
            config,
            request_id=task.request_id,
            error_code="UNEXPECTED_UI_FAILURE",
            error_detail=str(exc),
        )

    return mark_task_completed(
        config,
        request_id=task.request_id,
        output_path=result.output_path,
        elapsed_seconds=result.elapsed_seconds,
    )


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

    return _run_claimed_task(
        config=config,
        task=claimed_task,
        service=service,
        selected_model=selected,
        progress_callback=progress_callback,
    )


def process_next_queued_task(
    config: AppConfig,
    *,
    service: Service = run_upscale,
) -> TaskRecord | None:
    claimed_task = claim_next_queued_task(config)
    if claimed_task is None:
        return None
    return _run_claimed_task(config=config, task=claimed_task, service=service)


def ensure_background_worker(
    config: AppConfig,
    *,
    service: Service = run_upscale,
) -> BackgroundTaskWorker:
    worker_key = str(config.db_path.resolve())
    with _WORKERS_LOCK:
        worker = _WORKERS.get(worker_key)
        if worker is not None and worker.is_alive():
            return worker
        worker = BackgroundTaskWorker(config=config, service=service)
        worker.start()
        _WORKERS[worker_key] = worker
        return worker


def format_batch_queue_status(report: BatchTaskReport) -> str:
    queued = [task for task in report.tasks if task.status == "queued"]
    running = [task for task in report.tasks if task.status == "running"]
    lines = [
        f"批次编号：{report.batch_id}",
        f"总数：{len(report.tasks)}",
        f"已入队：{len(queued)}",
        f"处理中：{len(running)}",
        "处理方式：后台串行处理。提交后可以离开当前页面，稍后回来看结果。",
        "查看位置：右侧“任务”页会自动刷新状态；“日志”页可以看选中任务的请求日志。",
    ]
    if report.tasks:
        lines.append(f"首个任务：{report.tasks[0].request_id}")
    return "\n".join(lines)


def _merge_submit_and_selected_status(
    submit_status: str,
    selected_status: str,
    *,
    has_selected_task: bool,
) -> str:
    if not has_selected_task:
        return submit_status
    return f"{submit_status}\n\n当前任务\n{selected_status}"


def format_batch_status(report: BatchTaskReport) -> str:
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
    if completed and failed:
        lines.append("当前结果：部分完成。请在任务列表中查看失败项并决定是否重试。")
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


def handle_batch_enqueue(
    image_paths: object,
    model_id: str,
    output_format: str,
    quality: int,
    config: AppConfig,
    models: Sequence[ResolvedModel],
    progress: gr.Progress | None = None,
) -> tuple[str | None, str | None, str, str, str]:
    request_id = build_request_id()
    paths = _coerce_upload_paths(image_paths)
    if progress is None:
        progress = gr.Progress()
    progress(0.01, desc="请求已创建")

    if not paths:
        preview, download, status, request_log = _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="NO_IMAGE_SELECTED",
            user_message_zh="请先上传图片再开始放大。",
            likely_cause_zh="当前还没有选择任何输入图片。",
            suggested_action_zh="点击上传区域，选择一张或多张 PNG、JPG 或 WEBP 图片后重试。",
        )
        return preview, download, status, request_log, ""

    try:
        selected = next(model for model in models if model.id == model_id)
    except StopIteration:
        preview, download, status, request_log = _ui_error_with_log(
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
        return preview, download, status, request_log, ""
    if not selected.absolute_path.is_file():
        preview, download, status, request_log = _ui_error_with_log(
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
        return preview, download, status, request_log, ""

    persisted_inputs: list[Path] = []
    batch_id = build_batch_id()
    try:
        persisted_batch = _persist_batch_inputs(paths, config)
        persisted_inputs = [stored_input for _, stored_input in persisted_batch]
        queued_tasks = list(
            _queue_persisted_batch(
                config=config,
                batch_id=batch_id,
                model_id=model_id,
                output_format=output_format,
                quality=int(quality),
                persisted_inputs=persisted_batch,
            )
        )
    except Exception as exc:
        _unlink_paths(persisted_inputs)
        preview, download, status, request_log = _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="BATCH_QUEUE_SETUP_FAILED",
            user_message_zh="批量任务创建失败，暂时没有开始处理。",
            likely_cause_zh="输入文件持久化、任务写入或本地状态记录过程中发生错误。",
            suggested_action_zh="请重试一次；如果仍失败，请提供请求编号并查看 `logs/` 下的日志。",
            model_id=model_id,
            input_filename=paths[0].name,
            detail=str(exc),
        )
        return preview, download, status, request_log, ""

    progress(1.0, desc="任务已入队")
    report = BatchTaskReport(batch_id=batch_id, tasks=tuple(queued_tasks))
    selected_request_id = queued_tasks[0].request_id if queued_tasks else ""
    return (
        None,
        None,
        format_batch_queue_status(report),
        _batch_log_excerpt(config, queued_tasks),
        selected_request_id,
    )


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

    persisted_inputs: list[Path] = []
    batch_id = build_batch_id()
    try:
        persisted_batch = _persist_batch_inputs(paths, config)
        persisted_inputs = [stored_input for _, stored_input in persisted_batch]
        queued_tasks = list(
            _queue_persisted_batch(
                config=config,
                batch_id=batch_id,
                model_id=model_id,
                output_format=output_format,
                quality=int(quality),
                persisted_inputs=persisted_batch,
            )
        )
    except Exception as exc:
        _unlink_paths(persisted_inputs)
        return _ui_error_with_log(
            config=config,
            request_id=request_id,
            code="BATCH_QUEUE_SETUP_FAILED",
            user_message_zh="批量任务创建失败，暂时没有开始处理。",
            likely_cause_zh="输入文件持久化、任务写入或本地状态记录过程中发生错误。",
            suggested_action_zh="请重试一次；如果仍失败，请提供请求编号并查看 `logs/` 下的日志。",
            model_id=model_id,
            input_filename=paths[0].name,
            detail=str(exc),
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

    report = BatchTaskReport(batch_id=batch_id, tasks=tuple(processed_tasks))
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
    ensure_background_worker(runtime_config)
    initial_cleanup = cleanup_expired_history(runtime_config)
    installed_models = list_installed_models(runtime_config.models_dir)
    models = list_available_models(runtime_config.models_dir)
    hidden_local_models_count = max(0, len(installed_models) - len(models))
    choices = _model_choices(models)
    default_model = choices[0][1] if choices else None
    initial_status = "请上传图片，选择模型后提交。任务会在后台顺序处理。"
    if not choices:
        if installed_models:
            initial_status = (
                "当前本地已有模型，但还没有已验收并开放给日常操作的模型。"
                "请先完成本机验收，或调整开放状态后重启应用。"
            )
        else:
            initial_status = (
                "当前没有检测到已安装模型。请把模型文件放到 models 目录后重启应用。"
            )
    initial_guidance = format_model_guidance(
        default_model,
        models,
        has_local_models=bool(installed_models),
        hidden_local_models_count=hidden_local_models_count,
    )
    initial_tasks = list_tasks(runtime_config, limit=runtime_config.history_limit)
    initial_task_gallery = _task_gallery(initial_tasks)
    initial_task_state = _task_state(initial_tasks)
    initial_task_choices = _task_choices(initial_tasks)
    initial_task_list = _task_list_text(initial_tasks)
    initial_task_status = _task_summary(initial_tasks, initial_cleanup, runtime_config)
    initial_selected_task_id = initial_tasks[0].request_id if initial_tasks else ""

    def selected_task_values(request_id: str | None) -> tuple[str, str | None, str | None, str, str]:
        if not request_id:
            return (
                "",
                None,
                None,
                "请在任务列表里选择任务。这里会显示所选任务的详细状态、路径和错误信息。",
                "当前没有选中的任务日志。",
            )
        task = get_task(runtime_config, request_id)
        if task is None:
            return (
                "",
                None,
                None,
                "没有找到这条任务，列表可能已经刷新或任务已被删除。",
                "当前任务没有日志片段。",
            )
        preview_path = _task_preview_path(task)
        return (
            request_id,
            preview_path,
            preview_path,
            _task_detail(task),
            read_request_log_excerpt(runtime_config, request_id),
        )

    (
        initial_selected_task_id,
        initial_preview,
        initial_download,
        initial_task_detail,
        initial_logs,
    ) = selected_task_values(initial_selected_task_id)
    initial_selected_task = get_task(runtime_config, initial_selected_task_id)
    initial_live_status = _selected_task_status_text(initial_selected_task)

    def task_values(selected_request_id: str | None) -> tuple[
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
        str,
    ]:
        cleanup_result = cleanup_expired_history(runtime_config)
        tasks = list_tasks(runtime_config, limit=runtime_config.history_limit)
        task_choices = _task_choices(tasks)
        valid_ids = {task.request_id for task in tasks}
        active_id = (
            selected_request_id
            if selected_request_id and selected_request_id in valid_ids
            else (tasks[0].request_id if tasks else "")
        )
        selected_values = selected_task_values(active_id)
        active_task = get_task(runtime_config, active_id) if active_id else None
        return (
            _task_gallery(tasks),
            _task_state(tasks),
            _task_list_text(tasks),
            gr.update(
                choices=task_choices,
                value=active_id or None,
                interactive=bool(task_choices),
            ),
            selected_values[0],
            selected_values[1],
            selected_values[2],
            selected_values[3],
            selected_values[4],
            _task_summary(tasks, cleanup_result, runtime_config),
            _selected_task_status_text(active_task),
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
        str,
        str,
    ]:
        (
            preview,
            download,
            status_text,
            request_log,
            selected_request_id,
        ) = handle_batch_enqueue(
            image_paths=image_paths,
            model_id=model_id,
            output_format=output_format,
            quality=quality,
            config=runtime_config,
            models=models,
            progress=progress,
        )
        (
            gallery,
            state,
            task_list_text,
            choices_update,
            selected_request_id,
            selected_preview,
            selected_download,
            task_detail,
            selected_log,
            task_status,
            selected_status,
        ) = task_values(selected_request_id)
        preview = selected_preview if selected_preview is not None else preview
        download = selected_download if selected_download is not None else download
        request_log = selected_log if selected_request_id else request_log
        status_text = _merge_submit_and_selected_status(
            status_text,
            selected_status,
            has_selected_task=bool(selected_request_id),
        )
        return (
            preview,
            download,
            status_text,
            request_log,
            gallery,
            state,
            task_list_text,
            choices_update,
            selected_request_id,
            task_detail,
            task_status,
            selected_status,
        )

    def on_model_change(model_id: str) -> str:
        return format_model_guidance(
            model_id,
            models,
            has_local_models=bool(installed_models),
            hidden_local_models_count=hidden_local_models_count,
        )

    def on_task_select(
        request_id: str | None,
    ) -> tuple[str, str | None, str | None, str, str, str]:
        selected_request_id, preview_path, download_path, task_detail, request_log = (
            selected_task_values(request_id)
        )
        task = get_task(runtime_config, selected_request_id) if selected_request_id else None
        return (
            selected_request_id,
            preview_path,
            download_path,
            task_detail,
            request_log,
            _selected_task_status_text(task),
        )

    def on_task_refresh_selected(
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
        str,
    ]:
        return task_values(selected_request_id)

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
        str,
        str,
    ]:
        if not selected_request_id:
            (
                gallery,
                state,
                task_list_text,
                choices_update,
                active_id,
                preview,
                download,
                task_detail,
                request_log,
                task_status,
                selected_status,
            ) = task_values("")
            return (
                gallery,
                state,
                task_list_text,
                choices_update,
                active_id,
                preview,
                download,
                "请先在任务列表里选择要删除的任务。",
                request_log,
                task_detail,
                task_status,
                selected_status,
            )
        result = delete_task(runtime_config, selected_request_id)
        deleted_request_log = read_request_log_excerpt(runtime_config, selected_request_id)
        (
            gallery,
            state,
            task_list_text,
            choices_update,
            active_id,
            preview,
            download,
            task_detail,
            request_log,
            task_status,
            selected_status,
        ) = task_values("")
        return (
            gallery,
            state,
            task_list_text,
            choices_update,
            active_id,
            preview,
            download,
            result.message_zh,
            deleted_request_log if deleted_request_log else request_log,
            task_detail,
            task_status,
            selected_status,
        )

    with gr.Blocks(title="Pixloom", css=APP_CSS) as demo:
        gr.HTML(
            _shell_header_html(
                operator_count=len(models),
                installed_count=len(installed_models),
                hidden_local_models_count=hidden_local_models_count,
            )
        )
        selected_task_id = gr.State(initial_selected_task_id)
        task_state = gr.State(initial_task_state)
        with gr.Row(elem_classes="pix-main-grid"):
            with gr.Column(scale=5, min_width=320, elem_classes="pix-panel"):
                gr.HTML(
                    _panel_head_html(
                        "输入",
                        "提交任务",
                        "图片会先落到本地输入目录，再进入后台任务队列。",
                    )
                )
                image_input = gr.File(
                    label="上传图片（可多选）",
                    file_count="multiple",
                    file_types=[".png", ".jpg", ".jpeg", ".webp"],
                    type="filepath",
                    elem_id="pix-upload",
                )
                gr.HTML(
                    _panel_head_html(
                        "模型",
                        "选择策略",
                        "自然、锐化、动漫、快速试跑和慢速高质量分开摆，避免把风格差异埋进模型名里。",
                    )
                )
                model_input = gr.Dropdown(
                    label="模型",
                    choices=choices,
                    value=default_model,
                    interactive=bool(choices),
                    elem_id="pix-model-picker",
                )
                with gr.Accordion("模型与策略", open=True, elem_id="pix-model-accordion"):
                    model_guidance = gr.Markdown(value=initial_guidance, elem_id="pix-guidance")
                gr.HTML(
                    _panel_head_html(
                        "输出",
                        "保存参数",
                        "这里只保留格式和质量两个高频控制，减少手机端来回滚动。",
                    )
                )
                with gr.Accordion("输出参数", open=False, elem_id="pix-output-accordion"):
                    output_format = gr.Radio(
                        label="输出格式",
                        choices=["PNG", "JPG", "WEBP"],
                        value="PNG",
                        elem_id="pix-format",
                    )
                    quality = gr.Slider(
                        label="JPG / WEBP 质量",
                        minimum=1,
                        maximum=100,
                        value=90,
                        step=1,
                        elem_id="pix-quality",
                    )
                submit = gr.Button(
                    "提交任务",
                    variant="primary",
                    interactive=bool(choices),
                    elem_id="pix-submit-button",
                )
            with gr.Column(scale=6, min_width=360, elem_classes="pix-panel"):
                with gr.Tabs(elem_id="pix-results-tabs"):
                    with gr.Tab("结果"):
                        gr.HTML(
                            _panel_head_html(
                                "回执",
                                "当前结果",
                                "这里收口批次回执和当前选中任务的预览，不把队列细节塞进同一块区域。",
                            )
                        )
                        status = gr.Textbox(
                            label="批次回执",
                            lines=7,
                            value=initial_status,
                            elem_id="pix-status",
                        )
                        live_status = gr.Textbox(
                            label="当前任务状态",
                            lines=7,
                            value=initial_live_status,
                            elem_id="pix-live-status",
                        )
                        preview = gr.Image(
                            label="结果预览",
                            type="filepath",
                            value=initial_preview,
                            elem_id="pix-preview",
                        )
                        download = gr.File(
                            label="下载文件",
                            value=initial_download,
                            elem_id="pix-download",
                        )
                    with gr.Tab("任务"):
                        gr.HTML(
                            _panel_head_html(
                                "队列",
                                "任务状态",
                                "任务状态从 SQLite 回读。详情、列表和完成图都压成短区块，方便手机上扫一眼。",
                            )
                        )
                        task_status = gr.Textbox(
                            label="任务概览",
                            lines=3,
                            value=initial_task_status,
                            elem_id="pix-task-summary",
                        )
                        task_selector = gr.Dropdown(
                            label="选择任务",
                            choices=initial_task_choices,
                            value=initial_selected_task_id or None,
                            interactive=bool(initial_task_choices),
                            elem_id="pix-task-picker",
                        )
                        with gr.Accordion("所选任务详情", open=True, elem_id="pix-task-accordion"):
                            task_detail = gr.Textbox(
                                label="所选任务详情",
                                lines=9,
                                value=initial_task_detail,
                                elem_id="pix-task-detail",
                            )
                        task_list = gr.Textbox(
                            label="最近任务",
                            lines=8,
                            value=initial_task_list,
                            elem_id="pix-task-list",
                        )
                        with gr.Row():
                            refresh_tasks = gr.Button("刷新任务", elem_id="pix-refresh-button")
                            delete_selected_task = gr.Button(
                                "删除所选任务",
                                variant="stop",
                                elem_id="pix-delete-button",
                            )
                        with gr.Accordion("已完成图片", open=False, elem_id="pix-gallery-accordion"):
                            task_gallery = gr.Gallery(
                                label="已完成图片",
                                value=initial_task_gallery,
                                columns=3,
                                height=220,
                                allow_preview=True,
                                elem_id="pix-gallery",
                            )
                    with gr.Tab("日志"):
                        gr.HTML(
                            _panel_head_html(
                                "追踪",
                                "请求日志",
                                "按任务选择日志，排查时直接拿 request id 对照即可。",
                            )
                        )
                        request_logs = gr.Textbox(
                            label="所选任务日志",
                            lines=16,
                            value=initial_logs,
                            elem_id="pix-logs",
                        )
                refresh_timer = gr.Timer(value=3.0)

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
                    task_detail,
                    task_status,
                    live_status,
                ],
            )
        task_selector.change(
            fn=on_task_select,
            inputs=[task_selector],
            outputs=[
                selected_task_id,
                preview,
                download,
                task_detail,
                request_logs,
                live_status,
            ],
        )
        refresh_tasks.click(
            fn=on_task_refresh_selected,
            inputs=[selected_task_id],
            outputs=[
                task_gallery,
                task_state,
                task_list,
                task_selector,
                selected_task_id,
                preview,
                download,
                task_detail,
                request_logs,
                task_status,
                live_status,
            ],
        )
        refresh_timer.tick(
            fn=on_task_refresh_selected,
            inputs=[selected_task_id],
            outputs=[
                task_gallery,
                task_state,
                task_list,
                task_selector,
                selected_task_id,
                preview,
                download,
                task_detail,
                request_logs,
                task_status,
                live_status,
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
                task_detail,
                task_status,
                live_status,
            ],
        )

    return demo


def main() -> None:
    config = load_config()
    demo = build_demo(config)
    demo.queue(default_concurrency_limit=8).launch(
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
