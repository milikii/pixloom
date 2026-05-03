"""GET /api/health — liveness check."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.model_registry import list_available_models, list_installed_models

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(request: Request):
    config = request.app.state.config
    installed = list_installed_models(config.models_dir)
    available = list_available_models(config.models_dir)
    return {
        "status": "ok",
        "models_installed": len(installed),
        "models_operator": len(available),
    }
