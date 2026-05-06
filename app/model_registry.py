from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


BackendName = Literal["spandrel", "onnxruntime", "realesrgan", "custom"]
ExposureLevel = Literal["operator", "evaluation"]
ModelGroup = Literal[
    "photo-main",
    "photo-slow",
    "anime-main",
    "face-restoration",
    "quick-test",
    "classic-legacy",
]


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
    sharp_review_zh: str = ""
    group: ModelGroup = "classic-legacy"
    group_label_zh: str = ""
    group_order: int = 999
    sort_order: int = 999

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
            sharp_review_zh=self.sharp_review_zh,
            group=self.group,
            group_label_zh=self.group_label_zh,
            group_order=self.group_order,
            sort_order=self.sort_order,
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
    sharp_review_zh: str = ""
    group: ModelGroup = "classic-legacy"
    group_label_zh: str = ""
    group_order: int = 999
    sort_order: int = 999


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
            sharp_review_zh="稳，但不惊艳。照片修复的老黄牛，不会翻车但也不会给你惊喜。适合批量跑图，不求极致，只求不翻。",
            group="classic-legacy",
            group_label_zh="经典旧将",
            group_order=60,
            sort_order=10,
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
            sharp_review_zh="Real-ESRGAN 官方出品，通用性最强的照片模型。对压缩图片的修复稳定，但细节上限不如 UltraSharp。适合不知道选什么时无脑选。",
            group="classic-legacy",
            group_label_zh="经典旧将",
            group_order=60,
            sort_order=20,
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
            sharp_review_zh="🏆 摄影圈公认的最强泛用模型之一。边缘锐利到可以割手，抗 JPEG 伪影能力一绝，极少产生 AI 塑料感。真实风景和人物摄影的无脑首选。",
            group="classic-legacy",
            group_label_zh="经典旧将",
            group_order=60,
            sort_order=30,
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
            exposure="operator",
            display_name_zh="照片修复 - 4x NMKD-Siax",
            recommended_for_zh="适合压缩较重、带噪点或质量偏差的日常图片。",
            warning_zh="CPU 推理偏慢，但在 NAS 环境下可用。处理压缩图时去噪能力强于 UltraSharp。",
            speed_zh="普通偏慢",
            style_zh="修复/去噪",
            stability_zh="已本机验收",
            sharp_review_zh="🥈 去噪领域的隐藏BOSS。应对劣质源（过度压缩、带噪点的1080p图像）比 UltraSharp 更稳。纹理密集型写实图片的可靠选择。",
            group="photo-main",
            group_label_zh="照片主力",
            group_order=10,
            sort_order=30,
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
            sharp_review_zh="二次元专用，体积小跑得快。线条保护不错但别拿去跑真实照片——真人会变塑料娃娃。适合作为动漫批量处理的兜底选项。",
            group="anime-main",
            group_label_zh="动漫/线稿",
            group_order=30,
            sort_order=30,
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
            sharp_review_zh="轻量级的试跑选手。画质不顶尖但胜在快，CPU 上也能跑得动。适合先快速验证上传→队列→输出整个链路是否正常。",
            group="quick-test",
            group_label_zh="快速试跑",
            group_order=50,
            sort_order=10,
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
            enabled=True,
            exposure="operator",
            display_name_zh="SPAN 4x",
            recommended_for_zh="适合日常照片、通用图和想替换老 ESRGAN 的主力任务。",
            warning_zh="属于新一代轻量主力，但比快速试跑模型更慢；不适合做人脸专项修复。",
            speed_zh="普通",
            style_zh="照片主力",
            stability_zh="已本机验收",
            sharp_review_zh="🌟 轻量化新架构的黑马。速度显著优于传统 ESRGAN，画质持平甚至超越。在 i7-8700 纯 CPU 环境下，它是速度与质量的甜蜜点。",
            group="photo-main",
            group_label_zh="照片主力",
            group_order=10,
            sort_order=10,
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
            enabled=True,
            exposure="operator",
            display_name_zh="RealPLKSR 4x",
            recommended_for_zh="适合真实照片、风景、建筑和想用 2024 新架构替代老模型的主力任务。",
            warning_zh="更偏真实照片纹理重建，不是动漫专用；比快速试跑更慢，但应当优先于老 ESRGAN 尝试。",
            speed_zh="普通",
            style_zh="照片主力",
            stability_zh="已本机验收",
            sharp_review_zh="照片纹理重建的专家。对真实照片的细节还原能力强，但 CPU 推理速度中等偏慢。建议留给少量精品图慢慢跑。",
            group="photo-main",
            group_label_zh="照片主力",
            group_order=10,
            sort_order=20,
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
            enabled=True,
            exposure="evaluation",
            display_name_zh="DAT 4x",
            recommended_for_zh="实验模型，适合少量高质量通用图像对比测试。",
            warning_zh="参数体量巨大，1080p 到 4K 可能需 15 分钟以上。适合对时间不敏感的极限压榨任务。",
            speed_zh="很慢",
            style_zh="研究/通用",
            stability_zh="已本机验收",
            sharp_review_zh="学术界的画质 SOTA 选手。Transformer 架构，参数量巨大——1080p 到 4K 可能要 15 分钟以上。适合对时间完全不敏感的极限压榨。",
            group="photo-slow",
            group_label_zh="照片高质量慢跑",
            group_order=20,
            sort_order=30,
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
            sharp_review_zh="🏆 多项超分基准测试霸榜的 Transformer 模型。能「理解」图像全局结构，修复极其模糊的边缘。代价：纯 CPU 慢到令人发指，只适合真爱。",
            group="photo-slow",
            group_label_zh="照片高质量慢跑",
            group_order=20,
            sort_order=10,
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
            enabled=True,
            exposure="evaluation",
            display_name_zh="OmniSR 4x DF2K",
            recommended_for_zh="实验模型，适合极模糊原图的重建对比测试。",
            warning_zh="轻量化全向自注意力模型，模糊/低分辨率原图重建能力强。纯 CPU 偏慢但画质天花板高。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="已本机验收",
            sharp_review_zh="全向自注意力架构。极其模糊或低分辨率图像的重建能力惊人，细节还原度是天花板级别。DF2K 训练版，纯 CPU 请准备好耐心。",
            group="photo-slow",
            group_label_zh="照片高质量慢跑",
            group_order=20,
            sort_order=40,
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
            enabled=True,
            exposure="evaluation",
            display_name_zh="OmniSR X4 DIV2K",
            recommended_for_zh="实验模型，适合极模糊原图的重建对比测试。",
            warning_zh="safetensors 格式，OmniSR 架构的 DIV2K 训练版。模糊图重建能力突出，CPU 需耐心。",
            speed_zh="未知",
            style_zh="实验",
            stability_zh="已本机验收",
            sharp_review_zh="safetensors 格式的 OmniSR DIV2K 版。和 DF2K 版能力相近，模糊图重建能力突出。同样需要你在 CPU 面前保持信仰。",
            group="photo-slow",
            group_label_zh="照片高质量慢跑",
            group_order=20,
            sort_order=50,
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
            enabled=True,
            exposure="operator",
            display_name_zh="APISR 4x",
            recommended_for_zh="适合压缩较重的动漫、二次元图和希望保住线条结构的主力任务。",
            warning_zh="ONNX 动漫修复模型，适合压缩较重的二次元图片；不适合真实照片。",
            speed_zh="普通",
            style_zh="动漫修复",
            stability_zh="已后端接入",
            sharp_review_zh="🌟 二次元视频/图像超分的新晋神级模型。专门针对被过度压缩的动漫图像训练，识别和修复失真线条的能力极强。",
            group="anime-main",
            group_label_zh="动漫/线稿",
            group_order=30,
            sort_order=10,
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
            sharp_review_zh="🏆 B站开源镇馆之宝。对线条保护和色块平滑的处理至今难逢敌手，甚至能修复画师原画的作画瑕疵。二次元/线稿类图像的终极选择。",
            group="anime-main",
            group_label_zh="动漫/线稿",
            group_order=30,
            sort_order=20,
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
            enabled=True,
            exposure="operator",
            display_name_zh="CodeFormer",
            recommended_for_zh="适合老照片、小脸、压缩严重的人像修复，偏保真路线。",
            warning_zh="这是人脸修复，不是通用超分；没有明显人脸时请不要选它。",
            speed_zh="较慢",
            style_zh="人脸修复",
            stability_zh="已后端接入",
            sharp_review_zh="🌟 人脸保真度很强。可在“更像原图”和“更清晰”之间折中，AI 假面感低于老一代模型。",
            group="face-restoration",
            group_label_zh="人脸修复",
            group_order=40,
            sort_order=10,
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
            enabled=True,
            exposure="operator",
            display_name_zh="GFPGAN v1.4",
            recommended_for_zh="适合普通人像和低质量脸部修复，偏速度路线。",
            warning_zh="这是人脸修复，不是通用超分；没有明显人脸时请不要选它。",
            speed_zh="普通",
            style_zh="人脸修复",
            stability_zh="已后端接入",
            sharp_review_zh="🛡️ 老牌人脸修复，速度比 CodeFormer 更友好，适合作为轻量兜底选项。",
            group="face-restoration",
            group_label_zh="人脸修复",
            group_order=40,
            sort_order=20,
        ),
    )


def list_available_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    resolved = list_installed_models(models_dir, registry)
    visible = [
        model
        for model in resolved
        if model.enabled and model.exposure == "operator"
    ]
    return sorted(visible, key=lambda model: (model.group_order, model.sort_order, model.display_name_zh or model.display_name))


def list_installed_models(
    models_dir: Path,
    registry: tuple[ModelDefinition, ...] | None = None,
) -> list[ResolvedModel]:
    definitions = registry if registry is not None else get_default_registry()
    resolved = [definition.with_models_dir(models_dir) for definition in definitions]
    installed = [model for model in resolved if model.absolute_path.is_file()]
    return sorted(
        installed,
        key=lambda model: (model.group_order, model.sort_order, model.display_name_zh or model.display_name),
    )


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
