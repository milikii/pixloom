from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.config import AppConfig
from app.inference import (
    BackendRunner,
    InferenceError,
    UpscaleRequest,
    run_upscale,
    validate_upload,
)
from app.model_registry import ResolvedModel


class FakeBackend:
    def upscale(self, request: UpscaleRequest):
        with Image.open(request.input_path) as image:
            resized = image.resize(
                (image.width * request.model.scale, image.height * request.model.scale)
            )
        return resized


class FailingBackend:
    def upscale(self, request: UpscaleRequest):
        raise RuntimeError("backend exploded")


def _model(tmp_path: Path, backend: str = "spandrel") -> ResolvedModel:
    model_path = tmp_path / "model.pth"
    model_path.write_bytes(b"fake")
    return ResolvedModel(
        id="fake-4x",
        display_name="Fake 4x",
        backend=backend,  # type: ignore[arg-type]
        architecture="FakeSR",
        scale=4,
        path=Path("model.pth"),
        absolute_path=model_path,
        image_types=("test",),
        notes="test",
    )


def test_validate_upload_accepts_supported_images(tmp_path, tiny_png):
    result = validate_upload(tiny_png, AppConfig(input_dir=tmp_path))

    assert result.width == 8
    assert result.height == 6
    assert result.format == "PNG"


def test_validate_upload_rejects_unsupported_extension(tmp_path):
    path = tmp_path / "sample.gif"
    Image.new("RGB", (4, 4)).save(path)

    with pytest.raises(InferenceError, match="Supported formats"):
        validate_upload(path, AppConfig(input_dir=tmp_path))


def test_validate_upload_rejects_fake_image(tmp_path):
    path = tmp_path / "fake.png"
    path.write_text("not an image", encoding="utf-8")

    with pytest.raises(InferenceError, match="could not be decoded"):
        validate_upload(path, AppConfig(input_dir=tmp_path))


def test_validate_upload_rejects_large_image(tmp_path):
    path = tmp_path / "large.png"
    Image.new("RGB", (9, 4)).save(path)

    config = AppConfig(input_dir=tmp_path, max_input_side=8)

    with pytest.raises(InferenceError, match="exceeds the maximum input side"):
        validate_upload(path, config)


def test_validate_upload_rejects_oversized_file_before_decode(tmp_path):
    path = tmp_path / "large.png"
    path.write_bytes(b"x" * 11)

    config = AppConfig(input_dir=tmp_path, max_upload_bytes=10)

    with pytest.raises(InferenceError, match="maximum upload size"):
        validate_upload(path, config)


def test_run_upscale_with_fake_backend_writes_output(tmp_path, tiny_png):
    config = AppConfig(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        max_output_side=64,
    )

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(tmp_path),
        config=config,
        output_format="PNG",
        quality=90,
        backend=FakeBackend(),
    )

    assert result.input_size == (8, 6)
    assert result.output_size == (32, 24)
    assert result.model_name == "Fake 4x"
    assert result.output_path.is_file()
    assert result.elapsed_seconds >= 0


def test_run_upscale_rejects_too_large_output(tmp_path, tiny_png):
    config = AppConfig(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        max_output_side=16,
    )

    with pytest.raises(InferenceError, match="exceeds the maximum output side"):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FakeBackend(),
        )


def test_run_upscale_rejects_invalid_output_format_before_persisting_input(
    tmp_path, tiny_png
):
    config = AppConfig(input_dir=tmp_path / "input", output_dir=tmp_path / "output")

    with pytest.raises(InferenceError, match="Output format must be PNG, JPG, JPEG, or WEBP."):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="TIFF",
            quality=90,
            backend=FakeBackend(),
        )

    assert list(config.input_dir.iterdir()) == []


def test_run_upscale_maps_backend_failure_to_readable_error(tmp_path, tiny_png):
    config = AppConfig(input_dir=tmp_path / "input", output_dir=tmp_path / "output")

    with pytest.raises(InferenceError, match="Upscaling failed while running Fake 4x"):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path),
            config=config,
            output_format="PNG",
            quality=90,
            backend=FailingBackend(),
        )


def test_default_backend_runner_rejects_unimplemented_backend(tmp_path, tiny_png):
    config = AppConfig(input_dir=tmp_path / "input", output_dir=tmp_path / "output")

    with pytest.raises(InferenceError, match="Backend onnxruntime is not implemented"):
        run_upscale(
            image_path=tiny_png,
            original_name="sample.png",
            model=_model(tmp_path, backend="onnxruntime"),
            config=config,
            output_format="PNG",
            quality=90,
            backend=BackendRunner(),
        )


def test_default_backend_runner_delegates_to_spandrel_backend(monkeypatch, tmp_path, tiny_png):
    from app import spandrel_backend

    class FakeSpandrelBackend:
        def upscale(self, request: UpscaleRequest):
            with Image.open(request.input_path) as image:
                return image.resize((image.width * 4, image.height * 4))

    monkeypatch.setattr(spandrel_backend, "SpandrelBackend", FakeSpandrelBackend)

    config = AppConfig(input_dir=tmp_path / "input", output_dir=tmp_path / "output")

    result = run_upscale(
        image_path=tiny_png,
        original_name="sample.png",
        model=_model(tmp_path, backend="spandrel"),
        config=config,
        output_format="PNG",
        quality=90,
        backend=BackendRunner(),
    )

    assert result.output_size == (32, 24)
