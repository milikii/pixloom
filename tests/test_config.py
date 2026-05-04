from __future__ import annotations

from pathlib import Path

import pytest

from app.config import AppConfig, load_config


def test_load_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("PIXLOOM_MODELS_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_INPUT_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_LOGS_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_DB_PATH", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_INPUT_SIDE", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_OUTPUT_SIDE", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("PIXLOOM_TILE_SIZE", raising=False)
    monkeypatch.delenv("PIXLOOM_TILE_OVERLAP", raising=False)
    monkeypatch.delenv("PIXLOOM_HISTORY_LIMIT", raising=False)
    monkeypatch.delenv("PIXLOOM_HISTORY_RETENTION_DAYS", raising=False)

    config = load_config()

    assert config.models_dir == Path("models")
    assert config.input_dir == Path("input")
    assert config.output_dir == Path("output")
    assert config.logs_dir == Path("logs")
    assert config.db_path == Path("state/pixloom.sqlite3")
    assert config.max_input_side == 2048
    assert config.max_output_side == 8192
    assert config.max_upload_bytes == 25 * 1024 * 1024
    assert config.tile_size == 256
    assert config.tile_overlap == 16
    assert config.history_limit == 60
    assert config.history_retention_days == 0


def test_load_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("PIXLOOM_MODELS_DIR", str(tmp_path / "m"))
    monkeypatch.setenv("PIXLOOM_INPUT_DIR", str(tmp_path / "i"))
    monkeypatch.setenv("PIXLOOM_OUTPUT_DIR", str(tmp_path / "o"))
    monkeypatch.setenv("PIXLOOM_LOGS_DIR", str(tmp_path / "l"))
    monkeypatch.setenv("PIXLOOM_DB_PATH", str(tmp_path / "state" / "pixloom.sqlite3"))
    monkeypatch.setenv("PIXLOOM_MAX_INPUT_SIDE", "1024")
    monkeypatch.setenv("PIXLOOM_MAX_OUTPUT_SIDE", "4096")
    monkeypatch.setenv("PIXLOOM_MAX_UPLOAD_BYTES", "1048576")
    monkeypatch.setenv("PIXLOOM_TILE_SIZE", "128")
    monkeypatch.setenv("PIXLOOM_TILE_OVERLAP", "8")
    monkeypatch.setenv("PIXLOOM_HISTORY_LIMIT", "20")
    monkeypatch.setenv("PIXLOOM_HISTORY_RETENTION_DAYS", "14")

    config = load_config()

    assert config.models_dir == tmp_path / "m"
    assert config.input_dir == tmp_path / "i"
    assert config.output_dir == tmp_path / "o"
    assert config.logs_dir == tmp_path / "l"
    assert config.db_path == tmp_path / "state" / "pixloom.sqlite3"
    assert config.max_input_side == 1024
    assert config.max_output_side == 4096
    assert config.max_upload_bytes == 1048576
    assert config.tile_size == 128
    assert config.tile_overlap == 8
    assert config.history_limit == 20
    assert config.history_retention_days == 14


def test_app_config_ensures_directories(tmp_path):
    config = AppConfig(
        models_dir=tmp_path / "models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )

    config.ensure_directories()

    assert config.models_dir.is_dir()
    assert config.input_dir.is_dir()
    assert config.output_dir.is_dir()
    assert config.logs_dir.is_dir()
    assert config.db_path.parent.is_dir()


def test_load_config_accepts_zero_tile_overlap(monkeypatch):
    monkeypatch.setenv("PIXLOOM_TILE_OVERLAP", "0")

    config = load_config()

    assert config.tile_overlap == 0


def test_load_config_rejects_negative_tile_overlap(monkeypatch):
    monkeypatch.setenv("PIXLOOM_TILE_OVERLAP", "-1")

    with pytest.raises(ValueError, match="PIXLOOM_TILE_OVERLAP"):
        load_config()


def test_load_config_rejects_negative_history_retention(monkeypatch):
    monkeypatch.setenv("PIXLOOM_HISTORY_RETENTION_DAYS", "-1")

    with pytest.raises(ValueError, match="PIXLOOM_HISTORY_RETENTION_DAYS"):
        load_config()
