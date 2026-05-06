from __future__ import annotations

from app.bundled_models import sync_bundled_models
from app.config import AppConfig


def _config(tmp_path):
    return AppConfig(
        models_dir=tmp_path / "models",
        bundled_models_dir=tmp_path / "bundled-models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )


def test_sync_bundled_models_copies_missing_files(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.bundled_models_dir / "RealPLKSR_4x.pth").parent.mkdir(parents=True, exist_ok=True)
    (config.bundled_models_dir / "RealPLKSR_4x.pth").write_bytes(b"plksr")
    (config.bundled_models_dir / "facelib").mkdir(parents=True, exist_ok=True)
    (config.bundled_models_dir / "facelib" / "parsing_parsenet.pth").write_bytes(b"parse")

    result = sync_bundled_models(config)

    assert config.models_dir.joinpath("RealPLKSR_4x.pth").read_bytes() == b"plksr"
    assert config.models_dir.joinpath("facelib", "parsing_parsenet.pth").read_bytes() == b"parse"
    assert len(result.copied_files) == 2
    assert result.skipped_existing == ()


def test_sync_bundled_models_keeps_existing_runtime_files(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.bundled_models_dir / "RealPLKSR_4x.pth").parent.mkdir(parents=True, exist_ok=True)
    (config.bundled_models_dir / "RealPLKSR_4x.pth").write_bytes(b"bundled")
    (config.models_dir / "RealPLKSR_4x.pth").write_bytes(b"runtime")

    result = sync_bundled_models(config)

    assert config.models_dir.joinpath("RealPLKSR_4x.pth").read_bytes() == b"runtime"
    assert result.copied_files == ()
    assert result.skipped_existing == (config.models_dir / "RealPLKSR_4x.pth",)
