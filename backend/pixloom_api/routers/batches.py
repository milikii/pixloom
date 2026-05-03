"""POST /api/batches — create a batch with tasks (enqueue)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import AppConfig
from app.tasks import QueuedTaskInput, create_batch_with_tasks, build_batch_id
from app.request_logging import build_request_id, read_request_log_excerpt
from app.model_registry import list_available_models, ModelNotFoundError
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/batches", tags=["batches"])


class BatchCreateRequest(BaseModel):
    stored_paths: list[str]
    model_id: str
    output_format: str
    quality: int


@router.post("")
def create_batch(body: BatchCreateRequest, config: AppConfig = Depends(get_config)):
    if not body.stored_paths:
        return _batch_error("NO_IMAGE_SELECTED", "请先上传图片再开始放大。", "")

    models = list_available_models(config.models_dir)
    selected = next((m for m in models if m.id == body.model_id), None)
    if selected is None:
        return _batch_error(
            "MODEL_NOT_AVAILABLE", "当前选择的模型不可用。", body.model_id
        )
    if not selected.absolute_path.is_file():
        return _batch_error(
            "MODEL_FILE_MISSING", "当前模型文件不存在。", body.model_id
        )

    batch_id = build_batch_id()
    task_inputs = tuple(
        QueuedTaskInput(
            request_id=build_request_id(),
            input_filename=Path(p).name,
            input_path=Path(p),
            model_id=body.model_id,
            output_format=body.output_format,
            quality=body.quality,
        )
        for p in body.stored_paths
    )

    try:
        records = create_batch_with_tasks(
            config,
            batch_id=batch_id,
            model_id=body.model_id,
            output_format=body.output_format,
            quality=body.quality,
            tasks=task_inputs,
        )
    except Exception as exc:
        return _batch_error(
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
                "quality": r.quality,
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


def _batch_error(code: str, msg: str, model_id: str):
    return {
        "batch_id": "",
        "tasks": [],
        "queued_count": 0,
        "first_request_id": "",
        "status_message": f"错误 [{code}]：{msg}",
        "log_excerpt": f"[failure] batch_error | error_code={code} | model_id={model_id}",
    }
