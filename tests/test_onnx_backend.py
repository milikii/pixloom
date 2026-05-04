from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.config import AppConfig
from app.inference import UpscaleRequest
from app.model_registry import ResolvedModel
from app.onnx_backend import OnnxRuntimeBackend


class FakeInput:
    name = "pixel_values"


class FakeSession:
    def get_inputs(self):
        return [FakeInput()]

    def run(self, _, feed_dict):
        import numpy as np

        batch = feed_dict["pixel_values"]
        _, _, height, width = batch.shape
        output = np.ones((1, 3, height * 4, width * 4), dtype="float32") * 0.5
        return [output]


def test_onnx_backend_upscales_with_session_factory(tmp_path: Path):
    image_path = tmp_path / "sample.png"
    model_path = tmp_path / "model.onnx"
    Image.new("RGB", (8, 6), color=(20, 40, 60)).save(image_path)
    model_path.write_bytes(b"fake")

    request = UpscaleRequest(
        input_path=image_path,
        model=ResolvedModel(
            id="apisr-4x-int8",
            display_name="APISR",
            backend="onnxruntime",
            architecture="APISR",
            scale=4,
            path=Path("model.onnx"),
            absolute_path=model_path,
            image_types=("anime",),
            notes="test",
        ),
        config=AppConfig(tile_size=8, tile_overlap=0),
    )

    backend = OnnxRuntimeBackend(session_factory=lambda _: FakeSession())
    result = backend.upscale(request)

    assert result.size == (32, 24)
