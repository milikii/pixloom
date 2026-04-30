from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from app.config import AppConfig
from app.inference import InferenceError, validate_upload


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
