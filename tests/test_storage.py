from __future__ import annotations

import os
import time
from pathlib import Path

from app.config import AppConfig
from app.storage import (
    cleanup_stale_archives,
    cleanup_stale_thumbnails,
    collect_storage_snapshot,
)
from backend.pixloom_api.routers import storage as storage_router


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        models_dir=tmp_path / "models",
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        thumbnail_dir=tmp_path / "thumbnails",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
        history_retention_days=7,
        archive_ttl_hours=2,
    )


def test_collect_storage_snapshot_groups_managed_paths(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    (config.models_dir / "model.pth").write_bytes(b"model")
    (config.input_dir / "source.png").write_bytes(b"input")
    (config.output_dir / "result.png").write_bytes(b"output")
    (config.thumbnail_dir / "thumb.webp").write_bytes(b"thumb")
    (config.logs_dir / "pixloom-20260517.jsonl").write_bytes(b"log")
    config.db_path.write_bytes(b"sqlite")
    (config.output_dir.parent / "pixloom-results-old.zip").write_bytes(b"zip")

    snapshot = collect_storage_snapshot(config)
    categories = {category.key: category for category in snapshot.categories}

    assert snapshot.total_managed_bytes == sum(
        category.bytes for category in snapshot.categories
    )
    assert categories["models"].bytes == 5
    assert categories["input"].file_count == 1
    assert categories["output"].bytes == 6
    assert categories["thumbnails"].bytes == 5
    assert categories["logs"].bytes == 3
    assert categories["state"].bytes == 6
    assert categories["archives"].bytes == 3
    assert snapshot.retention.enabled
    assert snapshot.retention.archive_ttl_hours == 2


def test_cleanup_stale_archives_removes_only_expired_zip_files(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    old_archive = config.output_dir.parent / "pixloom-results-old.zip"
    fresh_archive = config.output_dir.parent / "pixloom-results-fresh.zip"
    old_archive.write_bytes(b"old")
    fresh_archive.write_bytes(b"fresh")
    old_time = time.time() - (3 * 60 * 60)
    os.utime(old_archive, (old_time, old_time))

    result = cleanup_stale_archives(config, now=time.time())

    assert result.deleted_paths == (old_archive,)
    assert result.bytes_deleted == 3
    assert not old_archive.exists()
    assert fresh_archive.exists()


def test_cleanup_stale_thumbnails_uses_history_retention_days(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    old_thumb = config.thumbnail_dir / "old.webp"
    fresh_thumb = config.thumbnail_dir / "fresh.webp"
    old_thumb.write_bytes(b"old")
    fresh_thumb.write_bytes(b"fresh")
    old_time = time.time() - (8 * 24 * 60 * 60)
    os.utime(old_thumb, (old_time, old_time))

    result = cleanup_stale_thumbnails(config, now=time.time())

    assert result.deleted_paths == (old_thumb,)
    assert result.bytes_deleted == 3
    assert not old_thumb.exists()
    assert fresh_thumb.exists()


def test_storage_endpoint_returns_cleanup_counters(tmp_path):
    config = _config(tmp_path)
    config.ensure_directories()
    old_archive = config.output_dir.parent / "pixloom-results-old.zip"
    old_archive.write_bytes(b"old")
    old_time = time.time() - (3 * 60 * 60)
    os.utime(old_archive, (old_time, old_time))

    body = storage_router.get_storage(config=config)

    assert body["retention"]["enabled"] is True
    assert body["cleanup"]["stale_archives_deleted"] == 1
    assert body["cleanup"]["stale_archive_bytes_deleted"] == 3
    assert any(category["key"] == "output" for category in body["categories"])
