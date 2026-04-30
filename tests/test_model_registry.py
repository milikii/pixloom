from __future__ import annotations

import pytest

from app.model_registry import (
    ModelNotFoundError,
    get_default_registry,
    list_available_models,
    resolve_model,
)


def test_list_available_models_returns_enabled_models_with_existing_files(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    (models_dir / "4x-UltraSharp.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == [
        "realesrgan-x4plus",
        "4x-ultrasharp",
    ]
    assert available[0].display_name == "Real-ESRGAN 4x Photo"
    assert available[0].backend == "spandrel"
    assert available[0].scale == 4


def test_list_available_models_hides_missing_and_disabled_models(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "future-span.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert available == []


def test_resolve_model_returns_existing_model(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "RealESRGAN_x4plus_anime_6B.pth").write_bytes(b"fake")

    model = resolve_model(
        "realesrgan-x4plus-anime",
        models_dir,
        get_default_registry(),
    )

    assert model.display_name == "Real-ESRGAN 4x Anime"
    assert model.absolute_path == models_dir / "RealESRGAN_x4plus_anime_6B.pth"


def test_resolve_model_rejects_unknown_model_id(tmp_path):
    with pytest.raises(ModelNotFoundError, match="Unknown model id: missing"):
        resolve_model("missing", tmp_path, get_default_registry())


def test_resolve_model_rejects_missing_model_file(tmp_path):
    with pytest.raises(ModelNotFoundError, match="Model file is missing"):
        resolve_model("realesrgan-x4plus", tmp_path, get_default_registry())
