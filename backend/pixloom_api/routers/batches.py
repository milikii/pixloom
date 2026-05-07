"""POST /api/batches — create a batch with tasks (enqueue)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import AppConfig
from app.output_size import (
    OUTPUT_SIZE_TARGETS,
    NATIVE_OUTPUT_SIZE_PRESET,
    normalize_output_size_preset,
    output_size_label_zh,
)
from app.output_quality import FIXED_OUTPUT_QUALITY, normalize_output_quality
from app.tasks import QueuedTaskInput, create_batch_with_tasks, build_batch_id
from app.request_logging import build_request_id, read_request_log_excerpt, log_event
from app.model_registry import list_available_models
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/batches", tags=["batches"])


class BatchCreateRequest(BaseModel):
    stored_paths: list[str]
    model_id: str
    output_format: str
    quality: int | None = None
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET


@router.post("")
def create_batch(body: BatchCreateRequest, config: AppConfig = Depends(get_config)):
    if not body.stored_paths:
        _batch_error(config, "NO_IMAGE_SELECTED", "请先上传图片再开始放大。", "")

    try:
        output_size_preset = normalize_output_size_preset(body.output_size_preset)
    except ValueError:
        allowed = ", ".join(OUTPUT_SIZE_TARGETS)
        _batch_error(
            config,
            "OUTPUT_SIZE_PRESET_INVALID",
            f"输出尺寸无效。可选值：{allowed}。",
            body.model_id,
        )

    models = list_available_models(config.models_dir)
    selected = next((m for m in models if m.id == body.model_id), None)
    if selected is None:
        _batch_error(
            config,
            "MODEL_NOT_AVAILABLE", "当前选择的模型不可用。", body.model_id
        )
    if not selected.absolute_path.is_file():
        _batch_error(
            config,
            "MODEL_FILE_MISSING", "当前模型文件不存在。", body.model_id
        )

    batch_id = build_batch_id()
    fixed_quality = normalize_output_quality(body.quality)
    task_inputs = tuple(
        QueuedTaskInput(
            request_id=build_request_id(),
            input_filename=Path(p).name,
            input_path=Path(p),
            model_id=body.model_id,
            output_format=body.output_format,
            quality=fixed_quality,
            output_size_preset=output_size_preset,
        )
        for p in body.stored_paths
    )

    try:
        records = create_batch_with_tasks(
            config,
            batch_id=batch_id,
            model_id=body.model_id,
            output_format=body.output_format,
            quality=fixed_quality,
            output_size_preset=output_size_preset,
            tasks=task_inputs,
        )
    except Exception as exc:
        _batch_error(
            config,
            "BATCH_QUEUE_SETUP_FAILED", f"批量任务创建失败：{exc}", body.model_id
        )

    first = records[0] if records else None
    log_excerpt = (
        read_request_log_excerpt(config, first.request_id) if first else ""
    )

    status_lines = [
        f"批次 ID: {batch_id}",
        f"共 {len(records)} 个任务已入队",
        "后台串行处理中。提交后可以离开本页面。",
    ]
    if first:
        status_lines.append(f"首个任务: {first.request_id}")

    return {
        "batch_id": batch_id,
        "tasks": [
            {
                "request_id": r.request_id,
                "batch_id": r.batch_id,
                "status": r.status,
                "status_label": "排队中",
                "input_filename": r.input_filename,
                "input_path": str(r.input_path),
                "output_path": str(r.output_path) if r.output_path else None,
                "model_id": r.model_id,
                "output_format": r.output_format,
                "quality": FIXED_OUTPUT_QUALITY,
                "output_size_preset": r.output_size_preset,
                "output_size_label": output_size_label_zh(r.output_size_preset),
                "created_at": r.created_at.isoformat(),
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "elapsed_seconds": r.elapsed_seconds,
                "progress_value": r.progress_value,
                "progress_step": r.progress_step,
                "progress_summary": "等待后台处理",
                "eta_seconds": None,
                "error_code": r.error_code,
                "error_detail": r.error_detail,
            }
            for r in records
        ],
        "queued_count": len(records),
        "first_request_id": first.request_id if first else "",
        "status_message": "\n".join(status_lines),
        "log_excerpt": log_excerpt,
    }


def _batch_error(config: AppConfig, code: str, msg: str, model_id: str) -> None:
    request_id = build_request_id()
    log_event(
        config,
        request_id=request_id,
        event="ui_rejected",
        status="failure",
        model_id=model_id,
        error_code=code,
        error_detail=msg,
    )
    raise HTTPException(
        status_code=400,
        detail={
            "request_id": request_id,
            "code": code,
            "user_message_zh": f"{msg} 请求编号：{request_id}",
            "likely_cause_zh": "请求在进入后台队列前被 API 边界拒绝。",
            "suggested_action_zh": "请按提示调整图片、模型或输出参数后重新提交。",
        },
    )
