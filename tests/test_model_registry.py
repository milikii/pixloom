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
    (models_dir / "SPAN_pretrain.pth").write_bytes(b"fake")
    (models_dir / "RealPLKSR_4x.pth").write_bytes(b"fake")
    (models_dir / "4x-UltraSharp.pth").write_bytes(b"fake")
    (models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    (models_dir / "RealESRGAN_x4plus_anime_6B.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == [
        "span-4x",
        "realplksr-4x",
        "4x-ultrasharp",
        "realesrgan-x4plus-anime",
        "realesrgan-x4plus",
    ]
    assert available[0].display_name == "SPAN 4x Pretrain"
    assert available[0].display_name_zh == "SPAN 4x"
    assert available[0].backend == "spandrel"
    assert available[0].scale == 4
    assert "日常照片" in available[0].recommended_for_zh
    assert available[0].style_zh == "照片主力"
    assert available[0].speed_zh == "普通"
    assert available[0].stability_zh == "已本机验收"
    assert available[0].exposure == "operator"
    assert available[0].group_label_zh == "照片主力"


def test_list_available_models_includes_promoted_spandrel_models(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "SPAN_pretrain.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == ["span-4x"]
    assert available[0].backend == "spandrel"
    assert available[0].exposure == "operator"
    assert available[0].group_label_zh == "照片主力"


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
    assert "动漫" in model.recommended_for_zh
    assert model.speed_zh == "较快"
    assert model.stability_zh == "已实机跑通"


def test_list_available_models_includes_real_cugan_and_hat_when_present(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "HAT-L-4x.pth").write_bytes(b"fake")
    (models_dir / "up3x-latest-denoise3x.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == [
        "hat-l-4x",
        "real-cugan-up3x-denoise3x",
    ]
    assert available[0].backend == "spandrel"
    assert available[0].speed_zh == "很慢"
    assert available[0].group_label_zh == "照片高质量慢跑"
    assert available[1].backend == "spandrel"
    assert available[1].scale == 3
    assert "3x" in available[1].warning_zh
    assert available[1].group_label_zh == "动漫/线稿"


def test_resolve_model_rejects_unknown_model_id(tmp_path):
    with pytest.raises(ModelNotFoundError, match="Unknown model id: missing"):
        resolve_model("missing", tmp_path, get_default_registry())


def test_resolve_model_rejects_missing_model_file(tmp_path):
    with pytest.raises(ModelNotFoundError, match="Model file is missing"):
        resolve_model("realesrgan-x4plus", tmp_path, get_default_registry())


def test_resolve_model_returns_promoted_spandrel_model(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "SPAN_pretrain.pth").write_bytes(b"fake")

    model = resolve_model("span-4x", models_dir, get_default_registry())

    assert model.id == "span-4x"
    assert model.backend == "spandrel"


def test_resolve_model_returns_onnx_model_when_operator_visible(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "APISR_4x_int8.onnx").write_bytes(b"fake")

    model = resolve_model("apisr-4x-int8", models_dir, get_default_registry())

    assert model.backend == "onnxruntime"
    assert model.architecture == "APISR"


def test_registry_functions_honor_explicit_empty_registry(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")

    assert list_available_models(models_dir, ()) == []

    with pytest.raises(ModelNotFoundError, match="Unknown model id: realesrgan-x4plus"):
        resolve_model("realesrgan-x4plus", models_dir, ())


def test_list_available_models_includes_newly_supported_backends(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "SPAN_pretrain.pth").write_bytes(b"fake")
    (models_dir / "RealPLKSR_4x.pth").write_bytes(b"fake")
    (models_dir / "4x_NMKD-Siax_200k.pth").write_bytes(b"fake")
    (models_dir / "4x-UltraSharp.pth").write_bytes(b"fake")
    (models_dir / "RealESRGAN_x4plus.pth").write_bytes(b"fake")
    (models_dir / "HAT-L-4x.pth").write_bytes(b"fake")
    (models_dir / "up3x-latest-denoise3x.pth").write_bytes(b"fake")
    (models_dir / "RealESRGAN_x4plus_anime_6B.pth").write_bytes(b"fake")
    (models_dir / "realesr-general-x4v3.pth").write_bytes(b"fake")
    (models_dir / "APISR_4x_int8.onnx").write_bytes(b"fake")
    (models_dir / "codeformer.pth").write_bytes(b"fake")
    (models_dir / "GFPGANv1.4.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == [
        "span-4x",
        "realplksr-4x",
        "4x-nmkd-siax-200k",
        "4x-ultrasharp",
        "hat-l-4x",
        "apisr-4x-int8",
        "real-cugan-up3x-denoise3x",
        "realesrgan-x4plus-anime",
        "codeformer",
        "gfpgan-v14",
        "realesr-general-x4v3",
        "realesrgan-x4plus",
    ]


def test_ultrasharp_is_grouped_as_photo_main(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "4x-UltraSharp.pth").write_bytes(b"fake")

    available = list_available_models(models_dir, get_default_registry())

    assert [model.id for model in available] == ["4x-ultrasharp"]
    assert available[0].group_label_zh == "照片主力"
    assert available[0].priority_stars == 4


def test_dat2_stays_in_registry_as_evaluation_model():
    dat2 = next(
        definition
        for definition in get_default_registry()
        if definition.id == "dat2-4x-pretrain"
    )
    assert dat2.group_label_zh == "照片高质量慢跑"
    assert dat2.exposure == "evaluation"
    assert "pretrain" in dat2.warning_zh
