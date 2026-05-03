"""GET /api/models — model listing and guidance."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import AppConfig
from app.model_registry import (
    list_available_models,
    list_installed_models,
    resolve_model,
)
from app.app import format_model_guidance
from backend.pixloom_api.deps import get_config

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
def get_models(config: AppConfig = Depends(get_config)):
    operator = list_available_models(config.models_dir)
    installed = list_installed_models(config.models_dir)
    hidden = max(0, len(installed) - len(operator))

    return {
        "models": [
            {
                "id": m.id,
                "display_name": m.display_name,
                "display_name_zh": m.display_name_zh,
                "backend": m.backend,
                "architecture": m.architecture,
                "scale": m.scale,
                "image_types": list(m.image_types),
                "recommended_for_zh": m.recommended_for_zh,
                "style_zh": m.style_zh,
                "speed_zh": m.speed_zh,
                "stability_zh": m.stability_zh,
                "warning_zh": m.warning_zh,
                "sharp_review_zh": m.sharp_review_zh,
                "notes": m.notes,
            }
            for m in operator
        ],
        "hidden_count": hidden,
    }


@router.get("/{model_id}/guidance")
def get_model_guidance(model_id: str, config: AppConfig = Depends(get_config)):
    installed = list_installed_models(config.models_dir)
    operator = list_available_models(config.models_dir)
    hidden = max(0, len(installed) - len(operator))

    guidance = format_model_guidance(
        model_id,
        operator,
        has_local_models=bool(installed),
        hidden_local_models_count=hidden,
    )
    return {"model_id": model_id, "guidance_markdown": guidance}
