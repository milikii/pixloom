from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BackendName = Literal["spandrel", "onnxruntime", "realesrgan"]


class ModelNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class ModelDefinition:
    id: str
    display_name: str
    backend: BackendName
    architecture: str
    scale: int
    path: Path
    image_types: tuple[str, ...]
    notes: str
    enabled: bool = True

    def with_models_dir(self, models_dir: Path) -> ResolvedModel:
        return ResolvedModel(
            id=self.id,
            display_name=self.display_name,
            backend=self.backend,
            architecture=self.architecture,
            scale=self.scale,
            path=self.path,
            absolute_path=models_dir / self.path,
            image_types=self.image_types,
            notes=self.notes,
            enabled=self.enabled,
        )


@dataclass(frozen=True)
class ResolvedModel:
    id: str
    display_name: str
    backend: BackendName
    architecture: str
    scale: int
    path: Path
    absolute_path: Path
    image_types: tuple[str, ...]
    notes: str
    enabled: bool = True


def get_default_registry() -> tuple[ModelDefinition, ...]:
    return (
        ModelDefinition(
            id="realesrgan-x4plus",
            display_name="Real-ESRGAN 4x Photo",
            backend="spandrel",
            architecture="RealESRGAN",
            scale=4,
            path=Path("RealESRGAN_x4plus.pth"),
            image_types=("photo", "general"),
            notes="Stable baseline for photos and compressed real-world images.",
        ),
        ModelDefinition(
            id="realesrgan-x4plus-anime",
            display_name="Real-ESRGAN 4x Anime",
            backend="spandrel",
            architecture="RealESRGAN",
            scale=4,
            path=Path("RealESRGAN_x4plus_anime_6B.pth"),
            image_types=("anime", "illustration", "line-art"),
            notes="Smaller anime and illustration baseline model.",
        ),
        ModelDefinition(
            id="realesr-general-x4v3",
            display_name="Real-ESRGAN General 4x v3",
            backend="spandrel",
            architecture="RealESRGAN",
            scale=4,
            path=Path("realesr-general-x4v3.pth"),
            image_types=("general", "fast-test"),
            notes="Lightweight baseline candidate for weaker CPUs.",
        ),
        ModelDefinition(
            id="4x-ultrasharp",
            display_name="4x UltraSharp",
            backend="spandrel",
            architecture="ESRGAN",
            scale=4,
            path=Path("4x-UltraSharp.pth"),
            image_types=("ai-art", "illustration", "general"),
            notes="Sharper visual style for AI images and illustration.",
        ),
        ModelDefinition(
            id="4x-remacri",
            display_name="4x Remacri",
            backend="spandrel",
            architecture="ESRGAN",
            scale=4,
            path=Path("4x_foolhardy_Remacri.pth"),
            image_types=("photo", "general"),
            notes="Natural-looking mature baseline for photos and mixed images.",
        ),
        ModelDefinition(
            id="span-4x",
            display_name="SPAN 4x",
            backend="spandrel",
            architecture="SPAN",
            scale=4,
            path=Path("SPAN_4x.pth"),
            image_types=("general", "anime", "ai-art"),
            notes="Second-phase model entry kept disabled until tested on CPU.",
            enabled=False,
        ),
        ModelDefinition(
            id="realplksr-4x",
            display_name="RealPLKSR 4x",
            backend="spandrel",
            architecture="RealPLKSR",
            scale=4,
            path=Path("RealPLKSR_4x.pth"),
            image_types=("photo", "general", "ai-art"),
            notes="Second-phase model entry kept disabled until model source is confirmed.",
            enabled=False,
        ),
    )


def list_available_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    definitions = registry or get_default_registry()
    resolved = [definition.with_models_dir(models_dir) for definition in definitions]
    return [
        model
        for model in resolved
        if model.enabled and model.absolute_path.is_file()
    ]


def resolve_model(
    model_id: str,
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> ResolvedModel:
    definitions = registry or get_default_registry()
    for definition in definitions:
        if definition.id == model_id:
            model = definition.with_models_dir(models_dir)
            if not model.enabled:
                raise ModelNotFoundError(f"Model is disabled: {model_id}")
            if not model.absolute_path.is_file():
                raise ModelNotFoundError(
                    f"Model file is missing for {model.display_name}: {model.absolute_path}"
                )
            return model
    raise ModelNotFoundError(f"Unknown model id: {model_id}")
