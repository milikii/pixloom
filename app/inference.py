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


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_SAVE_FORMATS = {"PNG", "JPG", "JPEG", "WEBP"}


class InferenceError(RuntimeError):
    pass


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


class UpscaleBackend(Protocol):
    def upscale(self, request: UpscaleRequest) -> Image.Image: ...


class BackendRunner:
    def upscale(self, request: UpscaleRequest) -> Image.Image:
        if request.model.backend == "spandrel":
            raise InferenceError("Spandrel backend is not wired yet.")
        raise InferenceError(f"Backend {request.model.backend} is not implemented in v1.")


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
        raise InferenceError("Supported formats are PNG, JPG, JPEG, and WEBP.")

    if path.stat().st_size > config.max_upload_bytes:
        raise InferenceError(
            f"Uploaded file exceeds the maximum upload size of {config.max_upload_bytes} bytes."
        )

    try:
        with Image.open(path) as image:
            image.load()
            width, height = image.size
            image_format = image.format or suffix.lstrip(".").upper()
    except (UnidentifiedImageError, OSError) as exc:
        raise InferenceError("The uploaded file could not be decoded as an image.") from exc

    if max(width, height) > config.max_input_side:
        raise InferenceError(
            f"Input image {width}x{height} exceeds the maximum input side "
            f"of {config.max_input_side}px."
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
        raise InferenceError("Output format must be PNG, JPG, JPEG, or WEBP.")
    if normalized == "JPG":
        return "JPEG"
    return normalized


def build_output_path(
    config: AppConfig,
    model: ResolvedModel,
    original_name: str,
    output_format: str,
) -> Path:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    save_format = normalize_output_format(output_format)
    extension = "jpg" if save_format == "JPEG" else save_format.lower()
    original_slug = _slug(original_name)
    filename = f"{_timestamp()}_{original_slug}_{model.id}_{model.scale}x.{extension}"
    return _unique_path(config.output_dir / filename)


def _save_image(image: Image.Image, output_path: Path, output_format: str, quality: int) -> None:
    save_format = normalize_output_format(output_format)
    save_kwargs: dict[str, int] = {}
    if save_format in {"JPEG", "WEBP"}:
        save_kwargs["quality"] = max(1, min(100, int(quality)))
    if save_format == "JPEG" and image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    image.save(output_path, format=save_format, **save_kwargs)


def run_upscale(
    image_path: Path,
    original_name: str,
    model: ResolvedModel,
    config: AppConfig,
    output_format: str,
    quality: int,
    backend: UpscaleBackend | None = None,
) -> UpscaleResult:
    config.ensure_directories()
    upload = validate_upload(image_path, config)
    expected_output_side = max(upload.width, upload.height) * model.scale
    if expected_output_side > config.max_output_side:
        raise InferenceError(
            f"Output side {expected_output_side}px exceeds the maximum output side "
            f"of {config.max_output_side}px."
        )

    stored_input = persist_upload(image_path, config, original_name)
    output_path = build_output_path(config, model, original_name, output_format)
    runner = backend or BackendRunner()
    started = time.perf_counter()

    try:
        output_image = runner.upscale(
            UpscaleRequest(input_path=stored_input, model=model, config=config)
        )
    except InferenceError:
        raise
    except Exception as exc:
        raise InferenceError(f"Upscaling failed while running {model.display_name}.") from exc

    try:
        _save_image(output_image, output_path, output_format, quality)
        output_size = output_image.size
    finally:
        output_image.close()

    elapsed = time.perf_counter() - started
    return UpscaleResult(
        input_path=stored_input,
        output_path=output_path,
        input_size=(upload.width, upload.height),
        output_size=output_size,
        model_name=model.display_name,
        elapsed_seconds=elapsed,
    )
