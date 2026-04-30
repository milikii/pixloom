from __future__ import annotations

from pathlib import Path

from PIL import Image

from app.config import AppConfig
from app.inference import build_output_path, persist_upload
from app.model_registry import ResolvedModel


def _model() -> ResolvedModel:
    return ResolvedModel(
        id="realesrgan-x4plus",
        display_name="Real-ESRGAN 4x Photo",
        backend="spandrel",
        architecture="RealESRGAN",
        scale=4,
        path=Path("RealESRGAN_x4plus.pth"),
        absolute_path=Path("models/RealESRGAN_x4plus.pth"),
        image_types=("photo",),
        notes="test",
    )


def test_persist_upload_saves_under_input_dir(tmp_path, tiny_png):
    config = AppConfig(input_dir=tmp_path / "input")
    config.ensure_directories()

    stored = persist_upload(tiny_png, config, original_name="../bad name.png")

    assert stored.parent == config.input_dir
    assert stored.name.endswith("_bad-name.png")
    assert stored.is_file()


def test_build_output_path_is_safe_and_descriptive(tmp_path):
    config = AppConfig(output_dir=tmp_path / "output")
    config.ensure_directories()

    output_path = build_output_path(
        config=config,
        model=_model(),
        original_name="../Summer Photo.JPG",
        output_format="WEBP",
    )

    assert output_path.parent == config.output_dir
    assert output_path.suffix == ".webp"
    assert "realesrgan-x4plus" in output_path.name
    assert "4x" in output_path.name
    assert "Summer-Photo" in output_path.name


def test_saved_output_can_be_written(tmp_path):
    config = AppConfig(output_dir=tmp_path / "output")
    config.ensure_directories()
    output_path = build_output_path(config, _model(), "sample.png", "PNG")

    Image.new("RGB", (4, 4)).save(output_path)

    assert output_path.is_file()
