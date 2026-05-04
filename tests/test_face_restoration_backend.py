from __future__ import annotations

from pathlib import Path

import pytest

from app.face_restoration_backend import ensure_face_support_files
from app.inference import InferenceError


def test_ensure_face_support_files_accepts_facelib_directory(tmp_path: Path):
    models_dir = tmp_path / "models"
    support_dir = models_dir / "facelib"
    support_dir.mkdir(parents=True)
    (support_dir / "detection_Resnet50_Final.pth").write_bytes(b"det")
    (support_dir / "parsing_parsenet.pth").write_bytes(b"parse")

    resolved = ensure_face_support_files(models_dir)

    assert resolved == support_dir
    assert (support_dir / "detection_Resnet50_Final.pth").is_file()
    assert (support_dir / "parsing_parsenet.pth").is_file()


def test_ensure_face_support_files_copies_legacy_root_files(tmp_path: Path):
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True)
    (models_dir / "detection_Resnet50_Final.pth").write_bytes(b"det")
    (models_dir / "parsing_parsenet.pth").write_bytes(b"parse")

    resolved = ensure_face_support_files(models_dir)

    assert resolved == models_dir / "facelib"
    assert (resolved / "detection_Resnet50_Final.pth").read_bytes() == b"det"
    assert (resolved / "parsing_parsenet.pth").read_bytes() == b"parse"


def test_ensure_face_support_files_rejects_missing_support_weights(tmp_path: Path):
    models_dir = tmp_path / "models"
    models_dir.mkdir(parents=True)

    with pytest.raises(InferenceError, match="Missing face restoration support files"):
        ensure_face_support_files(models_dir)
