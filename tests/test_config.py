from __future__ import annotations

from pathlib import Path

from app.config import AppConfig, load_config


def test_load_config_uses_defaults(monkeypatch):
    monkeypatch.delenv("PIXLOOM_MODELS_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_INPUT_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_LOGS_DIR", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_INPUT_SIDE", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_OUTPUT_SIDE", raising=False)
    monkeypatch.delenv("PIXLOOM_MAX_UPLOAD_BYTES", raising=False)
    monkeypatch.delenv("PIXLOOM_TILE_SIZE", raising=False)
    monkeypatch.delenv("PIXLOOM_TILE_OVERLAP", raising=False)
    monkeypatch.delenv("GRADIO_SERVER_NAME", raising=False)
    monkeypatch.delenv("GRADIO_SERVER_PORT", raising=False)
    monkeypatch.delenv("GRADIO_AUTH_USER", raising=False)
    monkeypatch.delenv("GRADIO_AUTH_PASS", raising=False)

    config = load_config()

    assert config.models_dir == Path("models")
    assert config.input_dir == Path("input")
    assert config.output_dir == Path("output")
    assert config.logs_dir == Path("logs")
    assert config.max_input_side == 2048
    assert config.max_output_side == 8192
    assert config.max_upload_bytes == 25 * 1024 * 1024
    assert config.tile_size == 256
    assert config.tile_overlap == 16
    assert config.server_name == "0.0.0.0"
    assert config.server_port == 7860
    assert config.gradio_auth is None


def test_load_config_reads_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("PIXLOOM_MODELS_DIR", str(tmp_path / "m"))
    monkeypatch.setenv("PIXLOOM_INPUT_DIR", str(tmp_path / "i"))
    monkeypatch.setenv("PIXLOOM_OUTPUT_DIR", str(tmp_path / "o"))
    monkeypatch.setenv("PIXLOOM_LOGS_DIR", str(tmp_path / "l"))
    monkeypatch.setenv("PIXLOOM_MAX_INPUT_SIDE", "1024")
    monkeypatch.setenv("PIXLOOM_MAX_OUTPUT_SIDE", "4096")
    monkeypatch.setenv("PIXLOOM_MAX_UPLOAD_BYTES", "1048576")
    monkeypatch.setenv("PIXLOOM_TILE_SIZE", "128")
    monkeypatch.setenv("PIXLOOM_TILE_OVERLAP", "8")
    monkeypatch.setenv("GRADIO_SERVER_NAME", "127.0.0.1")
    monkeypatch.setenv("GRADIO_SERVER_PORT", "9000")
    monkeypatch.setenv("GRADIO_AUTH_USER", "alice")
    monkeypatch.setenv("GRADIO_AUTH_PASS", "secret")

    config = load_config()

    assert config.models_dir == tmp_path / "m"
    assert config.input_dir == tmp_path / "i"
    assert config.output_dir == tmp_path / "o"
    assert config.logs_dir == tmp_path / "l"
    assert config.max_input_side == 1024
    assert config.max_output_side == 4096
    assert config.max_upload_bytes == 1048576
    assert config.tile_size == 128
    assert config.tile_overlap == 8
    assert config.server_name == "127.0.0.1"
    assert config.server_port == 9000
    assert config.gradio_auth == ("alice", "secret")


def test_app_config_ensures_directories(tmp_path):
    config = AppConfig(
        models_dir=tmp_path / "models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
    )

    config.ensure_directories()

    assert config.models_dir.is_dir()
    assert config.input_dir.is_dir()
    assert config.output_dir.is_dir()
    assert config.logs_dir.is_dir()
