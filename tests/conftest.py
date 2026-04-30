from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture()
def tiny_png(tmp_path: Path) -> Path:
    path = tmp_path / "sample.png"
    Image.new("RGB", (8, 6), color=(20, 40, 60)).save(path)
    return path


@pytest.fixture()
def tiny_jpg(tmp_path: Path) -> Path:
    path = tmp_path / "sample.jpg"
    Image.new("RGB", (5, 4), color=(80, 40, 20)).save(path, quality=90)
    return path
