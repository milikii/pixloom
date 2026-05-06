from __future__ import annotations

from pathlib import Path

from app.model_inventory import build_model_inventory, format_inventory_markdown


def test_build_model_inventory_marks_operator_and_evaluation_files(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    anime = models_dir / "RealESRGAN_x4plus_anime_6B.pth"
    general = models_dir / "realesr-general-x4v3.pth"
    remacri = models_dir / "4x_foolhardy_Remacri.pth"
    span = models_dir / "SPAN_pretrain.pth"
    untracked = models_dir / "custom.pth"
    anime.write_bytes(b"anime")
    general.write_bytes(b"general")
    remacri.write_bytes(b"remacri")
    span.write_bytes(b"span")
    untracked.write_bytes(b"custom")

    entries = build_model_inventory(models_dir)
    by_name = {entry.file_name: entry for entry in entries}

    assert by_name[anime.name].operator_visible is True
    assert by_name[anime.name].exposure == "operator"
    assert by_name[anime.name].display_name_zh == "动漫插画 - Real-ESRGAN Anime 6B"
    assert by_name[general.name].operator_visible is True
    assert by_name[general.name].display_name_zh == "快速试跑 - Real-ESRGAN General v3"
    assert by_name[remacri.name].operator_visible is True
    assert by_name[remacri.name].exposure == "operator"
    assert by_name[span.name].operator_visible is True
    assert by_name[span.name].exposure == "operator"
    assert by_name[span.name].stability_zh == "已本机验收"
    assert by_name[untracked.name].operator_visible is False
    assert by_name[untracked.name].exposure == "untracked"
    assert by_name[untracked.name].stability_zh == "未登记"


def test_format_inventory_markdown_renders_table(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    path = models_dir / "RealESRGAN_x4plus_anime_6B.pth"
    path.write_bytes(b"anime")

    markdown = format_inventory_markdown(build_model_inventory(models_dir))

    assert "Visible in dropdown" in markdown
    assert "`RealESRGAN_x4plus_anime_6B.pth`" in markdown
    assert "`yes`" in markdown
