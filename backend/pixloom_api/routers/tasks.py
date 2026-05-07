"""GET /api/tasks, DELETE /api/tasks/{request_id} — task listing and management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.config import AppConfig
from app.output_size import output_size_label_zh
from app.tasks import delete_task, get_task, list_tasks
from app.history import cleanup_expired_history
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/tasks", tags=["tasks"])

TASK_STATUS_LABELS = {
    "queued": "排队中",
    "running": "处理中",
    "completed": "已完成",
    "failed": "失败",
    "deleted": "已删除",
    "interrupted": "已中断",
}


def _task_progress_summary(task) -> str:
    if task.status == "queued":
        return "等待后台处理"
    if task.status == "running":
        pct = int(task.progress_value * 100)
        step = task.progress_step or ""
        eta = ""
        if task.progress_value > 0.05 and task.elapsed_seconds:
            eta_s = (task.elapsed_seconds / task.progress_value) - task.elapsed_seconds
            if eta_s > 0:
                eta = f" | 预计剩余 {_format_duration(eta_s)}"
        return f"{pct}% | {step}{eta}"
    if task.status == "completed":
        return "100% | 处理完成"
    if task.status == "failed":
        return f"处理失败 | {task.error_code}"
    return task.progress_step or "-"


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f} 秒"
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m} 分 {s} 秒"


def _task_to_dict(task) -> dict:
    return {
        "request_id": task.request_id,
        "batch_id": task.batch_id,
        "status": task.status,
        "status_label": TASK_STATUS_LABELS.get(task.status, task.status),
        "input_filename": task.input_filename,
        "input_path": str(task.input_path),
        "output_path": str(task.output_path) if task.output_path else None,
        "model_id": task.model_id,
        "output_format": task.output_format,
        "quality": task.quality,
        "output_size_preset": task.output_size_preset,
        "output_size_label": output_size_label_zh(task.output_size_preset),
        "created_at": task.created_at.isoformat(),
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "elapsed_seconds": task.elapsed_seconds,
        "progress_value": task.progress_value,
        "progress_step": task.progress_step,
        "progress_summary": _task_progress_summary(task),
        "eta_seconds": (
            ((task.elapsed_seconds / max(task.progress_value, 0.01)) - task.elapsed_seconds)
            if task.status == "running" and task.elapsed_seconds and task.progress_value > 0.05
            else None
        ),
        "error_code": task.error_code,
        "error_detail": task.error_detail,
    }


@router.get("")
def get_tasks(
    limit: int = Query(60, ge=1, le=200),
    config: AppConfig = Depends(get_config),
):
    cleanup = cleanup_expired_history(config)
    all_tasks = list_tasks(config, limit=limit)

    status_counts = {"total": 0, "queued": 0, "running": 0, "completed": 0,
                     "failed": 0, "deleted": 0, "interrupted": 0}
    for t in all_tasks:
        status_counts["total"] += 1
        key = t.status if t.status in status_counts else "total"
        if key != "total":
            status_counts[key] += 1

    cleanup_text = ""
    if config.history_retention_days > 0:
        pruned = len(cleanup.pruned_requests)
        cleanup_text = f"自动清理：保留最近 {config.history_retention_days} 天；本次清理 {pruned} 个文件。"
    else:
        cleanup_text = "自动清理：关闭。"

    return {
        "tasks": [_task_to_dict(t) for t in all_tasks],
        "summary": {**status_counts, "cleanup_text": cleanup_text},
    }


@router.delete("/{request_id}")
def delete_task_endpoint(request_id: str, config: AppConfig = Depends(get_config)):
    result = delete_task(config, request_id)
    return {
        "request_id": result.request_id,
        "deleted_paths": [str(path) for path in result.deleted_paths],
        "missing_paths": [str(path) for path in result.missing_paths],
        "skipped_paths": [str(path) for path in result.skipped_paths],
        "message_zh": result.message_zh,
    }
