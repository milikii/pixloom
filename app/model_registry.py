from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BackendName = Literal["spandrel", "onnxruntime", "realesrgan", "custom"]
ExposureLevel = Literal["operator", "evaluation"]


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
    exposure: ExposureLevel = "operator"
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
            exposure=self.exposure,
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
    exposure: ExposureLevel = "operator"
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
            exposure="operator",
            display_name_zh="照片自然 - 4x Remacri",
            recommended_for_zh="适合真实照片、人物、旅行照和想保留自然观感的混合图片。",
            warning_zh="通常更柔和，追求极致锐利或二次元线条时不如专用模型。",
            speed_zh="普通偏慢",
            style_zh="自然",
            stability_zh="已首轮实测",
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
            exposure="operator",
            display_name_zh="照片通用 - Real-ESRGAN 4x",
            recommended_for_zh="适合照片、压缩过的日常图片和多数通用场景。",
            warning_zh="细节会更自然，但插画和线稿不一定最锐利。",
            speed_zh="普通",
            style_zh="通用照片",
            stability_zh="已首轮实测",
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
            exposure="operator",
            display_name_zh="锐化插画 - 4x UltraSharp",
            recommended_for_zh="适合 AI 图、插画、压缩网图和希望边缘更锐利的图片。",
            warning_zh="锐化更强，真实照片可能出现偏硬或过锐的感觉。",
            speed_zh="普通偏慢",
            style_zh="锐利",
            stability_zh="已首轮实测",
        ),
        ModelDefinition(
            id="4x-nmkd-siax-200k",
            display_name="4x_NMKD-Siax_200k",
            backend="spandrel",
            architecture="ESRGAN",
            scale=4,
            path=Path("4x_NMKD-Siax_200k.pth"),
            image_types=("photo", "general", "compressed"),
            notes="Downloaded evaluation candidate for noisy or compressed real-world images.",
            exposure="evaluation",
            display_name_zh="照片修复 - 4x NMKD-Siax",
            recommended_for_zh="适合压缩较重、带噪点或质量偏差的日常图片。",
            warning_zh="当前阶段仅用于本机评估，还没有开放给日常操作。",
            speed_zh="普通偏慢",
            style_zh="修复/通用",
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
            display_name="SPAN 4x Pretrain",
            backend="spandrel",
            architecture="SPAN",
            scale=4,
            path=Path("SPAN_pretrain.pth"),
            image_types=("general", "anime", "ai-art"),
            notes="Downloaded SPAN-family pretrain kept disabled until tested on CPU.",
            enabled=False,
            exposure="evaluation",
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
            exposure="evaluation",
            display_name_zh="RealPLKSR 4x",
            recommended_for_zh="预留模型，适合照片、通用图和 AI 图片。",
            warning_zh="当前阶段未启用，模型来源与 CPU 表现还没确认。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="dat2-4x-pretrain",
            display_name="DAT2 4x Pretrain",
            backend="spandrel",
            architecture="DAT",
            scale=4,
            path=Path("DAT2_4x_pretrain.pth"),
            image_types=("photo", "general", "research"),
            notes="Downloaded DAT-family quality-ceiling evaluation weight.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="DAT 4x",
            recommended_for_zh="预留模型，适合高质量通用图像测试。",
            warning_zh="当前阶段仅用于本机评估，CPU 推理可能非常慢。",
            speed_zh="很慢",
            style_zh="研究/通用",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="hat-l-4x",
            display_name="HAT-L 4x",
            backend="spandrel",
            architecture="HAT",
            scale=4,
            path=Path("HAT-L-4x.pth"),
            image_types=("photo", "general", "research"),
            notes="Heavy HAT-family quality-ceiling weight kept available for operators who accept slower CPU runs.",
            enabled=True,
            exposure="operator",
            display_name_zh="质量上限 - HAT-L 4x",
            recommended_for_zh="适合追求细节上限的照片和通用图片，但更适合少量慢跑任务。",
            warning_zh="CPU 推理明显更慢，不适合大批量或手机上频繁试错。",
            speed_zh="很慢",
            style_zh="高质量上限",
            stability_zh="已本机加载，CPU 很慢",
        ),
        ModelDefinition(
            id="omnisr-4x-df2k",
            display_name="OmniSR 4x DF2K",
            backend="spandrel",
            architecture="OmniSR",
            scale=4,
            path=Path("OmniSR_4x_DF2K.pth"),
            image_types=("photo", "general", "research"),
            notes="Downloaded OmniSR evaluation weight from the DF2K release.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="OmniSR 4x DF2K",
            recommended_for_zh="预留模型，适合轻量化通用图像测试。",
            warning_zh="当前阶段仅用于本机评估，尚未开放到主流程。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="omnisr-x4-div2k",
            display_name="OmniSR X4 DIV2K",
            backend="spandrel",
            architecture="OmniSR",
            scale=4,
            path=Path("OmniSR_X4_DIV2K.safetensors"),
            image_types=("photo", "general", "research"),
            notes="Downloaded OmniSR evaluation weight in safetensors format.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="OmniSR X4 DIV2K",
            recommended_for_zh="预留模型，适合轻量化通用图像测试。",
            warning_zh="当前阶段仅用于本机评估，尚未开放到主流程。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="apisr-4x-int8",
            display_name="APISR 4x int8 ONNX",
            backend="onnxruntime",
            architecture="APISR",
            scale=4,
            path=Path("APISR_4x_int8.onnx"),
            image_types=("anime", "illustration", "restoration"),
            notes="Downloaded APISR-family ONNX evaluation weight.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="APISR 4x",
            recommended_for_zh="预留模型，适合动漫修复和线条保留测试。",
            warning_zh="当前阶段仅用于本机评估，需要单独后端接入。",
            speed_zh="未知",
            style_zh="动漫修复",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="real-cugan-up3x-denoise3x",
            display_name="Real-CUGAN up3x denoise3x",
            backend="spandrel",
            architecture="Real-CUGAN",
            scale=3,
            path=Path("up3x-latest-denoise3x.pth"),
            image_types=("anime", "manga", "restoration"),
            notes="Anime-leaning Real-CUGAN weight for denoise-focused 3x upscaling.",
            enabled=True,
            exposure="operator",
            display_name_zh="动漫修复 - Real-CUGAN 3x 去噪",
            recommended_for_zh="适合动漫、漫画、压缩动画帧和希望顺手做去噪的二次元图片。",
            warning_zh="这是 3x 模型，不是 4x；真实照片通常不如照片模型自然。",
            speed_zh="普通偏慢",
            style_zh="动漫去噪",
            stability_zh="已本机加载",
        ),
        ModelDefinition(
            id="codeformer",
            display_name="CodeFormer",
            backend="custom",
            architecture="CodeFormer",
            scale=1,
            path=Path("codeformer.pth"),
            image_types=("portrait", "face-restoration"),
            notes="Downloaded face-restoration evaluation weight.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="CodeFormer",
            recommended_for_zh="预留模型，适合人脸修复评估。",
            warning_zh="当前阶段仅用于本机评估，不属于主超分下拉框。",
            speed_zh="未知",
            style_zh="人脸修复",
            stability_zh="未启用",
        ),
        ModelDefinition(
            id="gfpgan-v14",
            display_name="GFPGAN v1.4",
            backend="custom",
            architecture="GFPGAN",
            scale=1,
            path=Path("GFPGANv1.4.pth"),
            image_types=("portrait", "face-restoration"),
            notes="Downloaded face-restoration baseline evaluation weight.",
            enabled=False,
            exposure="evaluation",
            display_name_zh="GFPGAN v1.4",
            recommended_for_zh="预留模型，适合人脸修复基线评估。",
            warning_zh="当前阶段仅用于本机评估，不属于主超分下拉框。",
            speed_zh="未知",
            style_zh="人脸修复",
            stability_zh="未启用",
        ),
    )


def list_available_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    resolved = list_installed_models(models_dir, registry)
    return [
        model
        for model in resolved
        if model.enabled and model.exposure == "operator"
    ]


def list_installed_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    definitions = registry if registry is not None else get_default_registry()
    resolved = [definition.with_models_dir(models_dir) for definition in definitions]
    return [model for model in resolved if model.absolute_path.is_file()]


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
            if model.exposure != "operator":
                raise ModelNotFoundError(f"Model is not operator-visible: {model_id}")
            if not model.absolute_path.is_file():
                raise ModelNotFoundError(
                    f"Model file is missing for {model.display_name}: {model.absolute_path}"
                )
            return model
    raise ModelNotFoundError(f"Unknown model id: {model_id}")
