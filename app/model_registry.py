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
    display_name_zh: str = ""
    recommended_for_zh: str = ""
    warning_zh: str = ""
    speed_zh: str = ""
    style_zh: str = ""
    stability_zh: str = ""

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
            display_name_zh=self.display_name_zh,
            recommended_for_zh=self.recommended_for_zh,
            warning_zh=self.warning_zh,
            speed_zh=self.speed_zh,
            style_zh=self.style_zh,
            stability_zh=self.stability_zh,
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
    display_name_zh: str = ""
    recommended_for_zh: str = ""
    warning_zh: str = ""
    speed_zh: str = ""
    style_zh: str = ""
    stability_zh: str = ""


def get_default_registry() -> tuple[ModelDefinition, ...]:
    return (
        ModelDefinition(
            id="4x-remacri",
            display_name="4x Remacri",
            backend="spandrel",
            architecture="ESRGAN",
            scale=4,
            path=Path("4x_foolhardy_Remacri.pth"),
            image_types=("photo", "portrait", "general"),
            notes="Natural-looking mature baseline for photos and mixed images.",
            display_name_zh="照片自然 - 4x Remacri",
            recommended_for_zh="适合真实照片、人物、旅行照和想保留自然观感的混合图片。",
            warning_zh="通常更柔和，追求极致锐利或二次元线条时不如专用模型。",
            speed_zh="普通偏慢",
            style_zh="自然",
            stability_zh="待本机验收",
        ),
        ModelDefinition(
            id="realesrgan-x4plus",
            display_name="Real-ESRGAN 4x Photo",
            backend="spandrel",
            architecture="RealESRGAN",
            scale=4,
            path=Path("RealESRGAN_x4plus.pth"),
            image_types=("photo", "general"),
            notes="Stable baseline for photos and compressed real-world images.",
            display_name_zh="照片通用 - Real-ESRGAN 4x",
            recommended_for_zh="适合照片、压缩过的日常图片和多数通用场景。",
            warning_zh="细节会更自然，但插画和线稿不一定最锐利。",
            speed_zh="普通",
            style_zh="通用照片",
            stability_zh="待本机验收",
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
            display_name_zh="锐化插画 - 4x UltraSharp",
            recommended_for_zh="适合 AI 图、插画、压缩网图和希望边缘更锐利的图片。",
            warning_zh="锐化更强，真实照片可能出现偏硬或过锐的感觉。",
            speed_zh="普通偏慢",
            style_zh="锐利",
            stability_zh="待本机验收",
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
            display_name_zh="动漫插画 - Real-ESRGAN Anime 6B",
            recommended_for_zh="适合动漫、插画、线稿和二次元风格图片。",
            warning_zh="处理真实照片时可能边缘偏硬，不一定最自然。",
            speed_zh="较快",
            style_zh="动漫/线稿",
            stability_zh="已实机跑通",
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
            display_name_zh="快速试跑 - Real-ESRGAN General v3",
            recommended_for_zh="适合先快速试跑，确认上传、队列和输出路径是否正常。",
            warning_zh="速度更友好，但细节上限通常低于更重的模型。",
            speed_zh="较快",
            style_zh="快速通用",
            stability_zh="已实机跑通",
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
            display_name_zh="SPAN 4x",
            recommended_for_zh="预留模型，适合通用、动漫和 AI 图片。",
            warning_zh="当前阶段未启用，等 CPU 实测后再开放。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="未启用",
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
            display_name_zh="RealPLKSR 4x",
            recommended_for_zh="预留模型，适合照片、通用图和 AI 图片。",
            warning_zh="当前阶段未启用，模型来源与 CPU 表现还没确认。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="未启用",
        ),
    )


def list_available_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    definitions = registry if registry is not None else get_default_registry()
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
    definitions = registry if registry is not None else get_default_registry()
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
