from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from PIL import Image

from app.inference import InferenceError, UpscaleRequest


FACE_SUPPORT_FILENAMES = (
    "detection_Resnet50_Final.pth",
    "parsing_parsenet.pth",
)


def ensure_face_support_files(models_dir: Path) -> Path:
    support_dir = models_dir / "facelib"
    support_dir.mkdir(parents=True, exist_ok=True)

    missing: list[str] = []
    for filename in FACE_SUPPORT_FILENAMES:
        support_path = support_dir / filename
        if support_path.is_file():
            continue
        legacy_path = models_dir / filename
        if legacy_path.is_file():
            shutil.copy2(legacy_path, support_path)
            continue
        missing.append(filename)

    if missing:
        joined = ", ".join(missing)
        raise InferenceError(
            code="MODEL_SUPPORT_FILE_MISSING",
            user_message_zh="人脸修复辅助模型文件缺失。",
            likely_cause_zh=f"当前缺少辅助权重：{joined}。",
            suggested_action_zh="请补齐 facelib 检测/解析权重后再试。",
            detail=f"Missing face restoration support files: {joined}",
        )

    return support_dir


class FaceRestorationBackend:
    def __init__(self) -> None:
        self._codeformer_cache: dict[tuple[str, int, int], Any] = {}
        self._codeformer_helper_cache: dict[str, Any] = {}
        self._gfpgan_cache: dict[tuple[str, int, int], Any] = {}

    def upscale(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        architecture = request.model.architecture.lower()
        if architecture == "codeformer":
            return self._run_codeformer(request, progress_callback=progress_callback)
        if architecture == "gfpgan":
            return self._run_gfpgan(request, progress_callback=progress_callback)
        raise InferenceError(
            code="CUSTOM_BACKEND_UNSUPPORTED",
            user_message_zh="当前自定义模型类型还没有接入。",
            likely_cause_zh=f"模型架构 {request.model.architecture} 没有对应的自定义后端实现。",
            suggested_action_zh="请改选其他模型，或继续补齐该模型的专用推理链路。",
            detail=f"Unsupported custom architecture: {request.model.architecture}",
        )

    def _run_codeformer(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        import cv2
        import torch
        from torchvision.transforms.functional import normalize

        from codeformer.basicsr.utils import img2tensor, tensor2img

        support_dir = ensure_face_support_files(request.config.models_dir)
        helper = self._load_codeformer_helper(support_dir)
        net = self._load_codeformer_net(request.model.absolute_path)

        image = cv2.imread(str(request.input_path), cv2.IMREAD_COLOR)
        if image is None:
            raise InferenceError(
                code="IMAGE_DECODE_FAILED",
                user_message_zh="图片文件无法被正确读取。",
                likely_cause_zh="OpenCV 无法解码当前输入图片。",
                suggested_action_zh="请换一张可正常打开的图片后再试。",
                detail=f"OpenCV failed to read image: {request.input_path}",
            )

        helper.clean_all()
        helper.read_image(image)
        if progress_callback is not None:
            progress_callback("正在检测人脸", 0.2)
        face_count = helper.get_face_landmarks_5(
            only_center_face=False,
            resize=640,
            eye_dist_threshold=5,
        )
        if face_count == 0:
            raise InferenceError(
                code="NO_FACE_DETECTED",
                user_message_zh="当前图片里没有检测到可修复的人脸。",
                likely_cause_zh="该模型只适合人脸修复，当前输入可能不是人物特写，或者脸部过小。",
                suggested_action_zh="请改用通用超分模型，或换一张脸部更清晰、更大的图片。",
                detail=f"No faces detected for {request.model.display_name}.",
            )
        helper.align_warp_face()

        for index, cropped_face in enumerate(helper.cropped_faces, start=1):
            if progress_callback is not None:
                progress = 0.3 + ((index - 1) / max(1, face_count)) * 0.45
                progress_callback(f"正在修复人脸 {index}/{face_count}", progress)

            cropped_face_tensor = img2tensor(cropped_face / 255.0, bgr2rgb=True, float32=True)
            normalize(
                cropped_face_tensor,
                (0.5, 0.5, 0.5),
                (0.5, 0.5, 0.5),
                inplace=True,
            )
            cropped_face_tensor = cropped_face_tensor.unsqueeze(0).to("cpu")

            try:
                with torch.no_grad():
                    output = net(cropped_face_tensor, w=0.5, adain=True)[0]
                restored_face = tensor2img(output, rgb2bgr=True, min_max=(-1, 1))
            except Exception as exc:
                raise InferenceError(
                    code="FACE_RESTORATION_FAILED",
                    user_message_zh="CodeFormer 人脸修复失败。",
                    likely_cause_zh="模型推理过程中发生了错误。",
                    suggested_action_zh="请稍后重试；如果重复失败，请换用 GFPGAN 或普通超分模型。",
                    detail=f"CodeFormer failed: {exc}",
                ) from exc

            helper.add_restored_face(restored_face.astype("uint8"), cropped_face)

        if progress_callback is not None:
            progress_callback("正在回贴修复结果", 0.82)
        helper.get_inverse_affine(None)
        restored_image = helper.paste_faces_to_input_image(upsample_img=None, draw_box=False)
        if progress_callback is not None:
            progress_callback("人脸修复完成，准备返回结果", 0.9)
        return Image.fromarray(cv2.cvtColor(restored_image, cv2.COLOR_BGR2RGB))

    def _run_gfpgan(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        import cv2

        _ensure_torchvision_functional_tensor_compat()
        from gfpgan.utils import GFPGANer
        import gfpgan.utils as gfpgan_utils

        support_dir = ensure_face_support_files(request.config.models_dir)
        restorer = self._load_gfpgan_restorer(
            request.model.absolute_path,
            support_dir,
            restorer_factory=GFPGANer,
            helper_module=gfpgan_utils,
        )

        image = cv2.imread(str(request.input_path), cv2.IMREAD_COLOR)
        if image is None:
            raise InferenceError(
                code="IMAGE_DECODE_FAILED",
                user_message_zh="图片文件无法被正确读取。",
                likely_cause_zh="OpenCV 无法解码当前输入图片。",
                suggested_action_zh="请换一张可正常打开的图片后再试。",
                detail=f"OpenCV failed to read image: {request.input_path}",
            )

        if progress_callback is not None:
            progress_callback("正在检测人脸", 0.2)
        _, restored_faces, restored_image = restorer.enhance(
            image,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
            weight=0.5,
        )
        if not restored_faces or restored_image is None:
            raise InferenceError(
                code="NO_FACE_DETECTED",
                user_message_zh="当前图片里没有检测到可修复的人脸。",
                likely_cause_zh="该模型只适合人脸修复，当前输入可能不是人物特写，或者脸部过小。",
                suggested_action_zh="请改用通用超分模型，或换一张脸部更清晰、更大的图片。",
                detail=f"No faces detected for {request.model.display_name}.",
            )

        if progress_callback is not None:
            progress_callback("人脸修复完成，准备返回结果", 0.9)
        return Image.fromarray(cv2.cvtColor(restored_image, cv2.COLOR_BGR2RGB))

    def _load_codeformer_helper(self, support_dir: Path) -> Any:
        key = str(support_dir.resolve())
        if key in self._codeformer_helper_cache:
            return self._codeformer_helper_cache[key]

        from codeformer.facelib import detection as detection_mod
        from codeformer.facelib import parsing as parsing_mod
        from codeformer.facelib.utils.face_restoration_helper import FaceRestoreHelper

        local_loader = _local_loader(support_dir)
        detection_mod.load_file_from_url = local_loader
        parsing_mod.load_file_from_url = local_loader

        helper = FaceRestoreHelper(
            1,
            face_size=512,
            crop_ratio=(1, 1),
            det_model="retinaface_resnet50",
            save_ext="png",
            use_parse=True,
            device="cpu",
        )
        self._codeformer_helper_cache[key] = helper
        return helper

    def _load_codeformer_net(self, model_path: Path) -> Any:
        import torch
        from codeformer.basicsr.utils.registry import ARCH_REGISTRY

        stat = model_path.stat()
        key = (str(model_path.resolve()), stat.st_mtime_ns, stat.st_size)
        if key in self._codeformer_cache:
            return self._codeformer_cache[key]

        network = ARCH_REGISTRY.get("CodeFormer")(
            dim_embd=512,
            codebook_size=1024,
            n_head=8,
            n_layers=9,
            connect_list=["32", "64", "128", "256"],
        ).to("cpu")

        checkpoint = torch.load(model_path, map_location="cpu")
        parameters = checkpoint.get("params_ema") or checkpoint.get("params") or checkpoint
        network.load_state_dict(parameters, strict=True)
        network.eval()
        self._codeformer_cache[key] = network
        return network

    def _load_gfpgan_restorer(
        self,
        model_path: Path,
        support_dir: Path,
        *,
        restorer_factory: Callable[..., Any],
        helper_module: Any,
    ) -> Any:
        stat = model_path.stat()
        key = (str(model_path.resolve()), stat.st_mtime_ns, stat.st_size)
        if key in self._gfpgan_cache:
            return self._gfpgan_cache[key]

        original_helper = helper_module.FaceRestoreHelper

        class LocalFaceRestoreHelper(original_helper):
            def __init__(self, *args, **kwargs):
                kwargs["model_rootpath"] = str(support_dir)
                super().__init__(*args, **kwargs)

        helper_module.FaceRestoreHelper = LocalFaceRestoreHelper
        try:
            restorer = restorer_factory(
                model_path=str(model_path),
                upscale=1,
                arch="clean",
                channel_multiplier=2,
                bg_upsampler=None,
                device="cpu",
            )
        finally:
            helper_module.FaceRestoreHelper = original_helper

        self._gfpgan_cache[key] = restorer
        return restorer


def _local_loader(support_dir: Path) -> Callable[..., str]:
    def load_file_from_url(url: str, model_dir=None, progress=True, file_name=None):  # noqa: ARG001
        filename = file_name or Path(url).name
        local_path = support_dir / filename
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        return str(local_path)

    return load_file_from_url


def _ensure_torchvision_functional_tensor_compat() -> None:
    module_name = "torchvision.transforms.functional_tensor"
    if module_name in sys.modules:
        return

    from torchvision.transforms import functional as functional_mod

    compatibility_module = ModuleType(module_name)
    compatibility_module.rgb_to_grayscale = functional_mod.rgb_to_grayscale
    sys.modules[module_name] = compatibility_module
