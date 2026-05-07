from __future__ import annotations

import re
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from PIL import Image, UnidentifiedImageError

from app.config import AppConfig
from app.model_registry import ResolvedModel
from app.output_size import (
    NATIVE_OUTPUT_SIZE_PRESET,
    OutputSizePlan,
    build_output_size_plan,
)
from app.output_quality import normalize_output_quality
from app.request_logging import build_request_id, log_event


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_SAVE_FORMATS = {"PNG", "JPG", "JPEG", "WEBP"}


class InferenceError(RuntimeError):
    def __init__(
        self,
        message: str | None = None,
        *,
        code: str = "INFERENCE_ERROR",
        user_message_zh: str | None = None,
        likely_cause_zh: str | None = None,
        suggested_action_zh: str | None = None,
        detail: str | None = None,
        request_id: str | None = None,
    ) -> None:
        resolved_message = user_message_zh or message or "处理失败。"
        super().__init__(detail or message or resolved_message)
        self.code = code
        self.user_message_zh = resolved_message
        self.likely_cause_zh = likely_cause_zh or "发生了未预期的处理问题。"
        self.suggested_action_zh = suggested_action_zh or "请稍后重试；如果重复失败，请提供请求编号排查。"
        self.detail = detail or message or resolved_message
        self.request_id = request_id


@dataclass(frozen=True)
class UploadInfo:
    path: Path
    width: int
    height: int
    format: str


@dataclass(frozen=True)
class UpscaleRequest:
    input_path: Path
    model: ResolvedModel
    config: AppConfig


@dataclass(frozen=True)
class UpscaleResult:
    input_path: Path
    output_path: Path
    input_size: tuple[int, int]
    output_size: tuple[int, int]
    model_name: str
    elapsed_seconds: float
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET
    target_longest_side: int | None = None
    request_id: str = ""


class UpscaleBackend(Protocol):
    def upscale(self, request: UpscaleRequest, progress_callback=None) -> Image.Image: ...


def _run_backend(
    backend: UpscaleBackend,
    request: UpscaleRequest,
    progress_callback=None,
) -> Image.Image:
    if progress_callback is None:
        return backend.upscale(request)
    try:
        return backend.upscale(request, progress_callback=progress_callback)
    except TypeError:
        return backend.upscale(request)


class BackendRunner:
    def __init__(self) -> None:
        self._spandrel_backend = None
        self._onnx_backend = None
        self._face_backend = None

    def upscale(self, request: UpscaleRequest, progress_callback=None) -> Image.Image:
        if request.model.backend == "spandrel":
            if self._spandrel_backend is None:
                from app.spandrel_backend import SpandrelBackend

                self._spandrel_backend = SpandrelBackend()
            return _run_backend(
                self._spandrel_backend,
                request,
                progress_callback=progress_callback,
            )
        if request.model.backend == "onnxruntime":
            if self._onnx_backend is None:
                from app.onnx_backend import OnnxRuntimeBackend

                self._onnx_backend = OnnxRuntimeBackend()
            return _run_backend(
                self._onnx_backend,
                request,
                progress_callback=progress_callback,
            )
        if request.model.backend == "custom":
            if self._face_backend is None:
                from app.face_restoration_backend import FaceRestorationBackend

                self._face_backend = FaceRestorationBackend()
            return _run_backend(
                self._face_backend,
                request,
                progress_callback=progress_callback,
            )
        raise InferenceError(
            code="BACKEND_NOT_IMPLEMENTED",
            user_message_zh="当前后端在 v1 里还没有实现。",
            likely_cause_zh=f"模型 {request.model.display_name} 依赖的后端 {request.model.backend} 还未接入。",
            suggested_action_zh="请改选当前已支持的模型，或等待后续版本补齐该后端。",
            detail=f"Backend {request.model.backend} is not implemented in v1.",
        )


def _slug(value: str) -> str:
    stem = Path(value).stem
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip(".-_")
    return slug or "image"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}-{counter}{path.suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def validate_upload(path: Path, config: AppConfig) -> UploadInfo:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise InferenceError(
            code="UNSUPPORTED_FORMAT",
            user_message_zh="暂不支持这种图片格式。",
            likely_cause_zh="当前只支持 PNG、JPG、JPEG 和 WEBP。",
            suggested_action_zh="请把图片转成 PNG、JPG、JPEG 或 WEBP 后再试。",
            detail="Supported formats are PNG, JPG, JPEG, and WEBP.",
        )

    if path.stat().st_size > config.max_upload_bytes:
        raise InferenceError(
            code="UPLOAD_TOO_LARGE",
            user_message_zh="上传文件超过大小限制。",
            likely_cause_zh=f"当前最大上传大小是 {config.max_upload_bytes} 字节。",
            suggested_action_zh="请压缩图片后重试，或调高 PIXLOOM_MAX_UPLOAD_BYTES。",
            detail=f"Uploaded file exceeds the maximum upload size of {config.max_upload_bytes} bytes.",
        )

    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            image_format = image.format or suffix.lstrip(".").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise InferenceError(
            code="IMAGE_DECODE_FAILED",
            user_message_zh="图片文件无法被正确读取。",
            likely_cause_zh="文件扩展名像图片，但实际内容损坏或不是有效图片。",
            suggested_action_zh="请换一张可正常打开的图片后再试。",
            detail="The uploaded file could not be decoded as an image.",
        ) from exc

    if max(width, height) > config.max_input_side:
        raise InferenceError(
            code="INPUT_TOO_LARGE",
            user_message_zh="输入图片尺寸超过当前限制。",
            likely_cause_zh=f"图片尺寸为 {width}x{height}，超过最长边 {config.max_input_side}px。",
            suggested_action_zh="请先缩小图片，或调高 PIXLOOM_MAX_INPUT_SIDE 后再试。",
            detail=(
                f"Input image {width}x{height} exceeds the maximum input side "
                f"of {config.max_input_side}px."
            ),
        )

    return UploadInfo(path=path, width=width, height=height, format=image_format)


def persist_upload(path: Path, config: AppConfig, original_name: str | None = None) -> Path:
    config.input_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _slug(original_name or path.name)
    suffix = path.suffix.lower()
    stored_path = _unique_path(config.input_dir / f"{_timestamp()}_{safe_name}{suffix}")
    shutil.copy2(path, stored_path)
    return stored_path


def normalize_output_format(output_format: str) -> str:
    normalized = output_format.upper()
    if normalized not in SUPPORTED_SAVE_FORMATS:
        raise InferenceError(
            code="OUTPUT_FORMAT_INVALID",
            user_message_zh="输出格式无效。",
            likely_cause_zh="当前只允许保存为 PNG、JPG、JPEG 或 WEBP。",
            suggested_action_zh="请改选 PNG、JPG 或 WEBP 后再试。",
            detail="Output format must be PNG, JPG, JPEG, or WEBP.",
        )
    if normalized == "JPG":
        return "JPEG"
    return normalized


def build_output_path(
    config: AppConfig,
    model: ResolvedModel,
    original_name: str,
    output_format: str,
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET,
) -> Path:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    save_format = normalize_output_format(output_format)
    extension = "jpg" if save_format == "JPEG" else save_format.lower()
    original_slug = _slug(original_name)
    preset_suffix = (
        ""
        if output_size_preset == NATIVE_OUTPUT_SIZE_PRESET
        else f"_{output_size_preset}"
    )
    filename = f"{_timestamp()}_{original_slug}_{model.id}_{model.scale}x{preset_suffix}.{extension}"
    return _unique_path(config.output_dir / filename)


def _save_image(image: Image.Image, output_path: Path, output_format: str, quality: int) -> None:
    save_format = normalize_output_format(output_format)
    save_kwargs: dict[str, int] = {}
    if save_format in {"JPEG", "WEBP"}:
        save_kwargs["quality"] = normalize_output_quality(quality)
    if save_format == "JPEG" and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    image.save(output_path, format=save_format, **save_kwargs)


def _unlink_if_exists(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _resize_image_file(
    input_path: Path,
    output_path: Path,
    size: tuple[int, int],
) -> None:
    with Image.open(input_path) as image:
        image.convert("RGB").resize(size, Image.Resampling.LANCZOS).save(output_path)


def _resize_output_image(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    if image.size == size:
        return image
    resized = image.resize(size, Image.Resampling.LANCZOS)
    image.close()
    return resized


def _prepared_input_path(config: AppConfig, request_token: str) -> Path:
    config.input_dir.mkdir(parents=True, exist_ok=True)
    return _unique_path(config.input_dir / f"{request_token}_prepared.png")


def _validate_output_size_plan(
    plan: OutputSizePlan,
    config: AppConfig,
) -> None:
    prepared_longest = max(plan.prepared_input_size)
    final_longest = max(plan.final_output_size)
    if prepared_longest > config.max_input_side:
        raise InferenceError(
            code="PREPARED_INPUT_TOO_LARGE",
            user_message_zh="目标尺寸需要的中间输入超过当前限制。",
            likely_cause_zh=(
                f"目标 {plan.label_zh} 需要先准备最长边 {prepared_longest}px 的中间图，"
                f"超过当前输入限制 {config.max_input_side}px。"
            ),
            suggested_action_zh="请改选较小的输出尺寸，或调高 PIXLOOM_MAX_INPUT_SIDE 后再试。",
            detail=(
                f"Prepared input side {prepared_longest}px exceeds the maximum input side "
                f"of {config.max_input_side}px."
            ),
        )
    if final_longest > config.max_output_side:
        raise InferenceError(
            code="OUTPUT_TOO_LARGE",
            user_message_zh="输出图片尺寸超过当前限制。",
            likely_cause_zh=(
                f"目标 {plan.label_zh} 的最长边为 {final_longest}px，"
                f"超过当前限制 {config.max_output_side}px。"
            ),
            suggested_action_zh="请改选较小的输出尺寸，或调高 PIXLOOM_MAX_OUTPUT_SIDE 后再试。",
            detail=(
                f"Output side {final_longest}px exceeds the maximum output side "
                f"of {config.max_output_side}px."
            ),
        )


def run_upscale(
    image_path: Path,
    original_name: str,
    model: ResolvedModel,
    config: AppConfig,
    output_format: str,
    quality: int,
    backend: UpscaleBackend | None = None,
    request_id: str | None = None,
    progress_callback=None,
    pre_persisted_input: bool = False,
    keep_input_on_failure: bool = False,
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET,
) -> UpscaleResult:
    request_token = request_id or build_request_id()
    config.ensure_directories()
    upload: UploadInfo | None = None
    stored_input: Path | None = None
    backend_input: Path | None = None
    prepared_input: Path | None = None
    output_path: Path | None = None
    size_plan: OutputSizePlan | None = None

    log_event(
        config,
        request_id=request_token,
        event="request_started",
        status="started",
        model_id=model.id,
        input_filename=original_name,
        output_size_preset=output_size_preset,
    )

    runner = backend or BackendRunner()
    try:
        upload = validate_upload(image_path, config)
        normalize_output_format(output_format)
        size_plan = build_output_size_plan(
            input_size=(upload.width, upload.height),
            model_scale=model.scale,
            preset=output_size_preset,
            max_prepared_input_side=config.max_input_side,
        )
        _validate_output_size_plan(size_plan, config)

        stored_input = (
            image_path
            if pre_persisted_input
            else persist_upload(image_path, config, original_name)
        )
        backend_input = stored_input
        if size_plan.requires_pre_resize:
            prepared_input = _prepared_input_path(config, request_token)
            if progress_callback is not None:
                progress_callback("正在准备目标尺寸", 0.1)
            _resize_image_file(stored_input, prepared_input, size_plan.prepared_input_size)
            backend_input = prepared_input

        output_path = build_output_path(
            config,
            model,
            original_name,
            output_format,
            output_size_preset=size_plan.preset,
        )
        log_event(
            config,
            request_id=request_token,
            event="inference_started",
            status="running",
            model_id=model.id,
            input_filename=original_name,
            input_path=stored_input,
            input_dimensions=(upload.width, upload.height),
            output_dimensions=size_plan.final_output_size,
            output_path=output_path,
            output_size_preset=size_plan.preset,
            target_longest_side=size_plan.target_longest_side,
        )
        started = time.perf_counter()
        if progress_callback is not None:
            progress_callback("准备开始推理", 0.15)
        output_image = _run_backend(
            runner,
            UpscaleRequest(input_path=backend_input, model=model, config=config),
            progress_callback=progress_callback,
        )
        try:
            if size_plan.requires_final_resize:
                if progress_callback is not None:
                    progress_callback("正在调整最终尺寸", 0.88)
                output_image = _resize_output_image(output_image, size_plan.final_output_size)
            if progress_callback is not None:
                progress_callback("正在写入输出文件", 0.92)
            _save_image(output_image, output_path, output_format, quality)
            output_size = output_image.size
        except Exception as exc:
            raise InferenceError(
                code="OUTPUT_SAVE_FAILED",
                user_message_zh="放大已完成，但保存结果文件失败。",
                likely_cause_zh="输出目录不可写、磁盘空间不足，或输出格式保存失败。",
                suggested_action_zh="请检查 `output/` 目录权限和磁盘空间后重试。",
                detail=f"Failed to save output image: {exc}",
                request_id=request_token,
            ) from exc
        finally:
            output_image.close()
        elapsed = time.perf_counter() - started
    except InferenceError as exc:
        exc.request_id = exc.request_id or request_token
        _unlink_if_exists(output_path)
        if not keep_input_on_failure:
            _unlink_if_exists(stored_input)
        log_event(
            config,
            request_id=request_token,
            event="request_failed",
            status="failure",
            model_id=model.id,
            input_filename=original_name,
            input_path=stored_input,
            input_dimensions=(upload.width, upload.height) if upload else None,
            output_dimensions=size_plan.final_output_size if size_plan else None,
            output_path=output_path,
            output_size_preset=size_plan.preset if size_plan else output_size_preset,
            target_longest_side=size_plan.target_longest_side if size_plan else None,
            error_code=exc.code,
            error_detail=exc.detail,
        )
        raise
    except Exception as exc:
        _unlink_if_exists(output_path)
        if not keep_input_on_failure:
            _unlink_if_exists(stored_input)
        wrapped = InferenceError(
            code="UPSCALE_FAILED",
            user_message_zh="放大处理失败。",
            likely_cause_zh="模型推理过程中发生了内部错误，或者当前模型文件不可用。",
            suggested_action_zh="请确认模型文件完整，再重试；如果重复失败，请提供请求编号排查。",
            detail=f"Upscaling failed while running {model.display_name}.",
            request_id=request_token,
        )
        log_event(
            config,
            request_id=request_token,
            event="request_failed",
            status="failure",
            model_id=model.id,
            input_filename=original_name,
            input_path=stored_input,
            input_dimensions=(upload.width, upload.height) if upload else None,
            output_dimensions=size_plan.final_output_size if size_plan else None,
            output_path=output_path,
            output_size_preset=size_plan.preset if size_plan else output_size_preset,
            target_longest_side=size_plan.target_longest_side if size_plan else None,
            error_code=wrapped.code,
            error_detail=f"{wrapped.detail} | {exc}",
        )
        raise wrapped from exc
    finally:
        _unlink_if_exists(prepared_input)

    log_event(
        config,
        request_id=request_token,
        event="request_succeeded",
        status="success",
        model_id=model.id,
        input_filename=original_name,
        input_path=stored_input,
        input_dimensions=(upload.width, upload.height),
        output_dimensions=output_size,
        output_path=output_path,
        output_size_preset=size_plan.preset if size_plan else output_size_preset,
        target_longest_side=size_plan.target_longest_side if size_plan else None,
        elapsed_seconds=elapsed,
    )
    if progress_callback is not None:
        progress_callback("处理完成", 1.0)
    return UpscaleResult(
        input_path=stored_input,
        output_path=output_path,
        input_size=(upload.width, upload.height),
        output_size=output_size,
        model_name=model.display_name_zh or model.display_name,
        elapsed_seconds=elapsed,
        output_size_preset=size_plan.preset if size_plan else output_size_preset,
        target_longest_side=size_plan.target_longest_side if size_plan else None,
        request_id=request_token,
    )
