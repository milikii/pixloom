from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import AppConfig


def build_request_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid4().hex[:8]}"


def log_event(
    config: AppConfig,
    *,
    request_id: str,
    event: str,
    status: str,
    model_id: str | None = None,
    input_filename: str | None = None,
    input_path: Path | None = None,
    input_dimensions: tuple[int, int] | None = None,
    output_dimensions: tuple[int, int] | None = None,
    output_path: Path | None = None,
    output_size_preset: str | None = None,
    target_longest_side: int | None = None,
    elapsed_seconds: float | None = None,
    error_code: str | None = None,
    error_detail: str | None = None,
) -> Path:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = config.logs_dir / f"pixloom-{datetime.now(timezone.utc):%Y%m%d}.jsonl"

    payload: dict[str, object] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "event": event,
        "status": status,
        "model_id": model_id or "",
        "input_filename": input_filename or "",
        "input_path": str(input_path) if input_path else "",
        "output_path": str(output_path) if output_path else "",
        "output_size_preset": output_size_preset or "",
        "target_longest_side": target_longest_side,
        "elapsed_seconds": elapsed_seconds,
        "error_code": error_code or "",
        "error_detail": error_detail or "",
    }
    if input_dimensions is not None:
        payload["input_dimensions"] = {
            "width": input_dimensions[0],
            "height": input_dimensions[1],
        }
    if output_dimensions is not None:
        payload["output_dimensions"] = {
            "width": output_dimensions[0],
            "height": output_dimensions[1],
        }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return log_path


def read_request_log_excerpt(config: AppConfig, request_id: str) -> str:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    events: list[str] = []
    for path in sorted(config.logs_dir.glob("pixloom-*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                if request_id not in raw_line:
                    continue
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                line = f"[{payload.get('status', '')}] {payload.get('event', '')}"
                if payload.get("elapsed_seconds") is not None:
                    line += f" | elapsed={payload['elapsed_seconds']}"
                if payload.get("error_code"):
                    line += f" | error_code={payload['error_code']}"
                if payload.get("error_detail"):
                    line += f" | detail={payload['error_detail']}"
                events.append(line)
    if not events:
        return "当前请求还没有日志片段。"
    return "\n".join(events)
