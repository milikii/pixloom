from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.config import AppConfig
from app.inference import InferenceError
from app.inference import UpscaleRequest
from app.model_registry import ResolvedModel
from app.spandrel_backend import SpandrelBackend


class FakeModel:
    scale = 2

    def eval(self):
        return self

    def to(self, device):
        self.device = device
        return self

    def __call__(self, tensor):
        import torch

        return torch.nn.functional.interpolate(
            tensor,
            scale_factor=2,
            mode="nearest",
        )


def _model(tmp_path: Path) -> ResolvedModel:
    model_path = tmp_path / "fake.pth"
    model_path.write_bytes(b"fake")
    return ResolvedModel(
        id="fake",
        display_name="Fake",
        backend="spandrel",
        architecture="FakeSR",
        scale=2,
        path=Path("fake.pth"),
        absolute_path=model_path,
        image_types=("test",),
        notes="test",
    )


def test_spandrel_backend_loads_model_once(monkeypatch, tmp_path, tiny_png):
    calls = []

    def fake_load_model(path):
        calls.append(path)
        return FakeModel()

    backend = SpandrelBackend(load_model=fake_load_model)
    request = UpscaleRequest(
        input_path=tiny_png,
        model=_model(tmp_path),
        config=AppConfig(tile_size=32, tile_overlap=0),
    )

    first = backend.upscale(request)
    second = backend.upscale(request)

    assert first.size == (16, 12)
    assert second.size == (16, 12)
    assert calls == [request.model.absolute_path]


def test_spandrel_backend_returns_rgb_image(monkeypatch, tmp_path, tiny_png):
    backend = SpandrelBackend(load_model=lambda path: FakeModel())
    request = UpscaleRequest(
        input_path=tiny_png,
        model=_model(tmp_path),
        config=AppConfig(tile_size=32, tile_overlap=0),
    )

    result = backend.upscale(request)

    assert isinstance(result, Image.Image)
    assert result.mode == "RGB"


def test_spandrel_backend_processes_multiple_tiles(tmp_path):
    calls = []

    class CountingModel(FakeModel):
        def __call__(self, tensor):
            calls.append(tuple(tensor.shape))
            return super().__call__(tensor)

    input_path = tmp_path / "wide.png"
    Image.new("RGB", (70, 40), color=(10, 20, 30)).save(input_path)
    backend = SpandrelBackend(load_model=lambda path: CountingModel())
    request = UpscaleRequest(
        input_path=input_path,
        model=_model(tmp_path),
        config=AppConfig(tile_size=32, tile_overlap=4),
    )

    result = backend.upscale(request)

    assert result.size == (140, 80)
    assert len(calls) > 1


def test_spandrel_backend_maps_loader_import_error(tmp_path, tiny_png):
    backend = SpandrelBackend(
        load_model=lambda path: (_ for _ in ()).throw(ImportError("missing spandrel"))
    )
    request = UpscaleRequest(
        input_path=tiny_png,
        model=_model(tmp_path),
        config=AppConfig(tile_size=32, tile_overlap=0),
    )

    with pytest.raises(InferenceError, match="must be installed for the spandrel backend"):
        backend.upscale(request)
