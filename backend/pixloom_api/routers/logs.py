"""GET /api/logs/{request_id} — JSONL audit log excerpt."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import AppConfig
from app.request_logging import read_request_log_excerpt
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/{request_id}")
def get_log_excerpt(request_id: str, config: AppConfig = Depends(get_config)):
    excerpt = read_request_log_excerpt(config, request_id)
    return {"request_id": request_id, "excerpt": excerpt}
