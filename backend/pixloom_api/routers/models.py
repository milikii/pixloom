"""GET /api/models — model listing and guidance."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import AppConfig
from app.model_registry import (
    list_available_models,
    list_installed_models,
)
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
                "group": m.group,
                "group_label_zh": m.group_label_zh,
                "group_order": m.group_order,
                "sort_order": m.sort_order,
                "priority_stars": m.priority_stars,
                "notes": m.notes,
            }
            for m in operator
        ],
        "hidden_count": hidden,
    }
