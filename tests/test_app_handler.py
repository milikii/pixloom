from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.app import handle_upscale
from app.config import AppConfig
from app.inference import InferenceError, UpscaleResult
from app.model_registry import ResolvedModel


class FakeService:
    def __init__(self, result: UpscaleResult | Exception):
        self.result = result
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _model(tmp_path: Path) -> ResolvedModel:
    model_path = tmp_path / "model.pth"
    model_path.write_bytes(b"fake")
    return ResolvedModel(
        id="fake-4x",
        display_name="Fake 4x",
        backend="spandrel",
        architecture="FakeSR",
        scale=4,
        path=Path("model.pth"),
        absolute_path=model_path,
        image_types=("test",),
        notes="test",
    )


def test_handle_upscale_returns_preview_download_and_status(tmp_path, tiny_png):
    output_path = tmp_path / "output.png"
    Image.new("RGB", (32, 24)).save(output_path)
    result = UpscaleResult(
        input_path=tiny_png,
        output_path=output_path,
        input_size=(8, 6),
        output_size=(32, 24),
        model_name="Fake 4x",
        elapsed_seconds=1.25,
    )
    service = FakeService(result)

    preview, download, status = handle_upscale(
        image_path=str(tiny_png),
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=AppConfig(models_dir=tmp_path),
        models=[_model(tmp_path)],
        service=service,
    )

    assert preview == str(output_path)
    assert download == str(output_path)
    assert "Fake 4x" in status
    assert "8x6" in status
    assert "32x24" in status
    assert "1.25s" in status
    assert service.calls == [
        {
            "image_path": tiny_png,
            "original_name": tiny_png.name,
            "model": _model(tmp_path),
            "config": AppConfig(models_dir=tmp_path),
            "output_format": "PNG",
            "quality": 90,
        }
    ]


def test_handle_upscale_maps_error_to_status(tmp_path, tiny_png):
    service = FakeService(InferenceError("boom"))

    preview, download, status = handle_upscale(
        image_path=str(tiny_png),
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=AppConfig(models_dir=tmp_path),
        models=[_model(tmp_path)],
        service=service,
    )

    assert preview is None
    assert download is None
    assert status == "Error: boom"
    assert len(service.calls) == 1


def test_handle_upscale_rejects_missing_image(tmp_path):
    preview, download, status = handle_upscale(
        image_path=None,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        config=AppConfig(models_dir=tmp_path),
        models=[],
    )

    assert preview is None
    assert download is None
    assert status == "Error: upload an image first."


def test_handle_upscale_rejects_unknown_model_id(tmp_path, tiny_png):
    preview, download, status = handle_upscale(
        image_path=str(tiny_png),
        model_id="missing",
        output_format="PNG",
        quality=90,
        config=AppConfig(models_dir=tmp_path),
        models=[_model(tmp_path)],
    )

    assert preview is None
    assert download is None
    assert status == "Error: selected model is not available: missing"


def test_handle_upscale_does_not_swallow_unexpected_runtime_error(tmp_path, tiny_png):
    with pytest.raises(RuntimeError, match="boom"):
        handle_upscale(
            image_path=str(tiny_png),
            model_id="fake-4x",
            output_format="PNG",
            quality=90,
            config=AppConfig(models_dir=tmp_path),
            models=[_model(tmp_path)],
            service=FakeService(RuntimeError("boom")),
        )
