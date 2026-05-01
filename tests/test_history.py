from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from PIL import Image

from app.config import AppConfig
from app.history import (
    cleanup_expired_history,
    delete_history_item,
    list_history_items,
)
from app.request_logging import log_event


def _config(tmp_path, retention_days: int = 0) -> AppConfig:
    return AppConfig(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        logs_dir=tmp_path / "logs",
        history_retention_days=retention_days,
    )


def _image(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (4, 4)).save(path)
    return path


def _write_success_log(
    config: AppConfig,
    *,
    request_id: str,
    timestamp: datetime,
    input_path,
    output_path,
) -> None:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": timestamp.isoformat(),
        "request_id": request_id,
        "event": "request_succeeded",
        "status": "success",
        "model_id": "fake-4x",
        "input_filename": input_path.name,
        "input_path": str(input_path),
        "output_path": str(output_path),
        "elapsed_seconds": 1.25,
        "error_code": "",
        "error_detail": "",
    }
    with (config.logs_dir / "pixloom-20260430.jsonl").open(
        "a", encoding="utf-8"
    ) as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def test_list_history_items_uses_success_logs_and_existing_output(tmp_path):
    config = _config(tmp_path)
    input_path = _image(config.input_dir / "source.png")
    output_path = _image(config.output_dir / "result.png")
    log_event(
        config,
        request_id="req-1",
        event="request_succeeded",
        status="success",
        model_id="fake-4x",
        input_filename="source.png",
        input_path=input_path,
        output_path=output_path,
        elapsed_seconds=1.25,
    )

    items = list_history_items(config)

    assert len(items) == 1
    assert items[0].request_id == "req-1"
    assert items[0].input_path == input_path.resolve()
    assert items[0].output_path == output_path.resolve()
    assert items[0].elapsed_seconds == 1.25


def test_delete_history_item_removes_input_and_output_then_hides_item(tmp_path):
    config = _config(tmp_path)
    input_path = _image(config.input_dir / "source.png")
    output_path = _image(config.output_dir / "result.png")
    log_event(
        config,
        request_id="req-delete",
        event="request_succeeded",
        status="success",
        model_id="fake-4x",
        input_filename="source.png",
        input_path=input_path,
        output_path=output_path,
        elapsed_seconds=1.25,
    )

    result = delete_history_item(config, "req-delete")

    assert "已删除历史任务" in result.message_zh
    assert not input_path.exists()
    assert not output_path.exists()
    assert list_history_items(config) == []
    log_text = next(config.logs_dir.glob("pixloom-*.jsonl")).read_text(encoding="utf-8")
    assert '"event": "history_deleted"' in log_text


def test_cleanup_expired_history_deletes_old_items_and_keeps_recent(tmp_path):
    now = datetime.now(timezone.utc)
    config = _config(tmp_path, retention_days=7)
    old_input = _image(config.input_dir / "old-source.png")
    old_output = _image(config.output_dir / "old-result.png")
    recent_input = _image(config.input_dir / "recent-source.png")
    recent_output = _image(config.output_dir / "recent-result.png")
    _write_success_log(
        config,
        request_id="old",
        timestamp=now - timedelta(days=10),
        input_path=old_input,
        output_path=old_output,
    )
    _write_success_log(
        config,
        request_id="recent",
        timestamp=now,
        input_path=recent_input,
        output_path=recent_output,
    )

    result = cleanup_expired_history(config)

    assert not result.skipped
    assert "old" in result.pruned_requests
    assert not old_input.exists()
    assert not old_output.exists()
    assert recent_input.exists()
    assert recent_output.exists()
    assert [item.request_id for item in list_history_items(config)] == ["recent"]


def test_cleanup_expired_history_is_disabled_when_retention_is_zero(tmp_path):
    now = datetime.now(timezone.utc)
    config = _config(tmp_path, retention_days=0)
    input_path = _image(config.input_dir / "source.png")
    output_path = _image(config.output_dir / "result.png")
    _write_success_log(
        config,
        request_id="kept",
        timestamp=now - timedelta(days=30),
        input_path=input_path,
        output_path=output_path,
    )

    result = cleanup_expired_history(config)

    assert result.skipped
    assert input_path.exists()
    assert output_path.exists()
