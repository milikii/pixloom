from __future__ import annotations

from fastapi import Request

from app.config import AppConfig


def get_config(request: Request) -> AppConfig:
    return request.app.state.config
