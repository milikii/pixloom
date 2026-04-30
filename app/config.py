from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    models_dir: Path = Path("models")
    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    logs_dir: Path = Path("logs")
    max_input_side: int = 2048
    max_output_side: int = 8192
    max_upload_bytes: int = 25 * 1024 * 1024
    tile_size: int = 256
    tile_overlap: int = 16
    server_name: str = "0.0.0.0"
    server_port: int = 7860
    gradio_auth: tuple[str, str] | None = None

    def ensure_directories(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


def _env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default))


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _env_non_negative_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    value = int(raw)
    if value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _load_gradio_auth() -> tuple[str, str] | None:
    username = os.environ.get("GRADIO_AUTH_USER", "").strip()
    password = os.environ.get("GRADIO_AUTH_PASS", "")
    if not username and not password:
        return None
    if not username or not password:
        raise ValueError("GRADIO_AUTH_USER and GRADIO_AUTH_PASS must be set together")
    return (username, password)


def load_config() -> AppConfig:
    return AppConfig(
        models_dir=_env_path("PIXLOOM_MODELS_DIR", "models"),
        input_dir=_env_path("PIXLOOM_INPUT_DIR", "input"),
        output_dir=_env_path("PIXLOOM_OUTPUT_DIR", "output"),
        logs_dir=_env_path("PIXLOOM_LOGS_DIR", "logs"),
        max_input_side=_env_int("PIXLOOM_MAX_INPUT_SIDE", 2048),
        max_output_side=_env_int("PIXLOOM_MAX_OUTPUT_SIDE", 8192),
        max_upload_bytes=_env_int("PIXLOOM_MAX_UPLOAD_BYTES", 25 * 1024 * 1024),
        tile_size=_env_int("PIXLOOM_TILE_SIZE", 256),
        tile_overlap=_env_non_negative_int("PIXLOOM_TILE_OVERLAP", 16),
        server_name=os.environ.get("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=_env_int("GRADIO_SERVER_PORT", 7860),
        gradio_auth=_load_gradio_auth(),
    )
