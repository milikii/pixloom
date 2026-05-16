from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.config import AppConfig
from app.storage import thumbnail_cache_path
from app.tasks import (
    claim_next_queued_task,
    claim_queued_task,
    QueuedTaskInput,
    create_batch_with_tasks,
    create_batch,
    delete_task,
    enqueue_task,
    get_task,
    initialize_task_store,
    list_tasks,
    mark_running_tasks_interrupted,
    mark_task_completed,
    mark_task_failed,
    update_task_progress,
)


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
        thumbnail_dir=tmp_path / "thumbnails",
        logs_dir=tmp_path / "logs",
        db_path=tmp_path / "state" / "pixloom.sqlite3",
    )


def _create_batch(config: AppConfig, batch_id: str = "batch-1") -> None:
    create_batch(
        config,
        batch_id=batch_id,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        total_count=1,
    )


def test_initialize_task_store_creates_sqlite_file(tmp_path):
    config = _config(tmp_path)

    initialize_task_store(config)

    assert config.db_path.is_file()


def test_enqueue_and_claim_task_transitions_to_running(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)

    queued = enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claimed = claim_queued_task(config, "req-1")

    assert queued.status == "queued"
    assert queued.output_size_preset == "native"
    assert claimed is not None
    assert claimed.status == "running"
    assert claimed.started_at is not None
    assert claim_queued_task(config, "req-1") is None


def test_tasks_persist_quality_as_100(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)

    queued = enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="JPG",
        quality=90,
    )

    assert queued.quality == 100


def test_claim_next_queued_task_is_transactional_by_status(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )

    first = claim_next_queued_task(config)
    second = claim_next_queued_task(config)

    assert first is not None
    assert first.request_id == "req-1"
    assert second is None


def test_mark_task_completed_records_output_and_elapsed_time(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    output_path = config.output_dir / "result.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    output_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")

    completed = mark_task_completed(
        config,
        request_id="req-1",
        output_path=output_path,
        elapsed_seconds=1.25,
    )

    assert completed.status == "completed"
    assert completed.output_path == output_path
    assert completed.elapsed_seconds == 1.25
    assert completed.completed_at is not None


def test_mark_task_failed_keeps_error_fields_visible(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")

    failed = mark_task_failed(
        config,
        request_id="req-1",
        error_code="UPSCALE_FAILED",
        error_detail="backend exploded",
    )

    assert failed.status == "failed"
    assert failed.error_code == "UPSCALE_FAILED"
    assert failed.error_detail == "backend exploded"
    assert failed.completed_at is not None


def test_update_task_progress_persists_step_and_percent(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")

    updated = update_task_progress(
        config,
        request_id="req-1",
        progress_value=0.42,
        progress_step="正在处理分块 2/5",
    )

    assert updated.progress_value == 0.42
    assert updated.progress_step == "正在处理分块 2/5"


def test_mark_running_tasks_interrupted_after_restart(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")

    changed = mark_running_tasks_interrupted(config)
    task = get_task(config, "req-1")

    assert changed == 1
    assert task is not None
    assert task.status == "interrupted"
    assert task.error_code == "TASK_INTERRUPTED"


def test_list_tasks_filters_statuses(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )

    assert [task.request_id for task in list_tasks(config, statuses=("queued",))] == [
        "req-1"
    ]
    assert list_tasks(config, statuses=("failed",)) == []


def test_delete_task_removes_safe_input_and_output_files(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    output_path = config.output_dir / "result.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"input")
    output_path.write_bytes(b"output")
    thumbnail_path = thumbnail_cache_path(config, output_path, 160)
    thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
    thumbnail_path.write_bytes(b"thumbnail")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=input_path,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")
    mark_task_completed(
        config,
        request_id="req-1",
        output_path=output_path,
        elapsed_seconds=1.25,
    )

    result = delete_task(config, "req-1")
    task = get_task(config, "req-1")

    assert task is not None
    assert task.status == "deleted"
    assert input_path in result.deleted_paths
    assert output_path in result.deleted_paths
    assert thumbnail_path in result.deleted_paths
    assert not input_path.exists()
    assert not output_path.exists()
    assert not thumbnail_path.exists()
    assert "已删除任务：req-1" in result.message_zh

    log_text = next(config.logs_dir.glob("pixloom-*.jsonl")).read_text(encoding="utf-8")
    assert '"event": "task_deleted"' in log_text


def test_delete_task_skips_paths_outside_runtime_directories(tmp_path):
    config = _config(tmp_path)
    outside_input = tmp_path / "outside-input.png"
    outside_output = tmp_path / "outside-output.png"
    outside_input.write_bytes(b"input")
    outside_output.write_bytes(b"output")
    _create_batch(config)
    enqueue_task(
        config,
        request_id="req-1",
        batch_id="batch-1",
        input_filename="source.png",
        input_path=outside_input,
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
    )
    claim_queued_task(config, "req-1")
    mark_task_completed(
        config,
        request_id="req-1",
        output_path=outside_output,
        elapsed_seconds=1.25,
    )

    result = delete_task(config, "req-1")
    task = get_task(config, "req-1")

    assert task is not None
    assert task.status == "deleted"
    assert outside_input.exists()
    assert outside_output.exists()


def test_create_batch_with_tasks_is_atomic_on_failure(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")

    original_connect = __import__("app.tasks", fromlist=["_connect"])._connect

    class BrokenConnection:
        def __init__(self, real):
            self._real = real
            self._insert_count = 0
            self.isolation_level = None

        def execute(self, sql, params=()):
            if "INSERT INTO tasks" in sql:
                self._insert_count += 1
                if self._insert_count == 2:
                    raise sqlite3.OperationalError("boom")
            return self._real.execute(sql, params)

        def __getattr__(self, name):
            return getattr(self._real, name)

        def __enter__(self):
            self._real.__enter__()
            return self

        def __exit__(self, exc_type, exc, tb):
            return self._real.__exit__(exc_type, exc, tb)

    def broken_connect(cfg):
        return BrokenConnection(original_connect(cfg))

    import app.tasks as tasks_module

    tasks_module._connect = broken_connect
    try:
        with pytest.raises(sqlite3.OperationalError, match="boom"):
            create_batch_with_tasks(
                config,
                batch_id="batch-1",
                model_id="fake-4x",
                output_format="PNG",
                quality=90,
                tasks=(
                    QueuedTaskInput(
                        request_id="req-1",
                        input_filename="source.png",
                        input_path=input_path,
                        model_id="fake-4x",
                        output_format="PNG",
                        quality=90,
                    ),
                    QueuedTaskInput(
                        request_id="req-2",
                        input_filename="source-2.png",
                        input_path=input_path,
                        model_id="fake-4x",
                        output_format="PNG",
                        quality=90,
                    ),
                ),
            )
    finally:
        tasks_module._connect = original_connect

    assert list_tasks(config) == []


def test_create_batch_with_tasks_persists_output_size_preset(tmp_path):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")

    records = create_batch_with_tasks(
        config,
        batch_id="batch-1",
        model_id="fake-4x",
        output_format="PNG",
        quality=90,
        output_size_preset="4k",
        tasks=(
            QueuedTaskInput(
                request_id="req-1",
                input_filename="source.png",
                input_path=input_path,
                model_id="fake-4x",
                output_format="PNG",
                quality=90,
                output_size_preset="4k",
            ),
        ),
    )

    assert records[0].output_size_preset == "4k"
    assert list_tasks(config)[0].output_size_preset == "4k"


def test_initialize_task_store_migrates_output_size_preset_columns(tmp_path):
    config = _config(tmp_path)
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(config.db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE batches (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                model_id TEXT NOT NULL,
                output_format TEXT NOT NULL,
                quality INTEGER NOT NULL,
                total_count INTEGER NOT NULL
            );
            CREATE TABLE tasks (
                request_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_filename TEXT NOT NULL,
                input_path TEXT NOT NULL,
                output_path TEXT NOT NULL DEFAULT '',
                model_id TEXT NOT NULL,
                output_format TEXT NOT NULL,
                quality INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL DEFAULT '',
                elapsed_seconds REAL,
                progress_value REAL NOT NULL DEFAULT 0,
                progress_step TEXT NOT NULL DEFAULT '',
                error_code TEXT NOT NULL DEFAULT '',
                error_detail TEXT NOT NULL DEFAULT '',
                retry_of_request_id TEXT NOT NULL DEFAULT ''
            );
            """
        )

    initialize_task_store(config)

    with sqlite3.connect(config.db_path) as connection:
        batch_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(batches)")
        }
        task_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(tasks)")
        }

    assert "output_size_preset" in batch_columns
    assert "output_size_preset" in task_columns


def test_create_batch_with_tasks_rolls_back_when_queue_logging_fails(tmp_path, monkeypatch):
    config = _config(tmp_path)
    input_path = config.input_dir / "source.png"
    input_path.parent.mkdir(parents=True, exist_ok=True)
    input_path.write_bytes(b"fake")

    import app.tasks as tasks_module

    def failing_log_event(*args, **kwargs):
        raise RuntimeError("log failed")

    monkeypatch.setattr(tasks_module, "log_event", failing_log_event)

    with pytest.raises(RuntimeError, match="log failed"):
        create_batch_with_tasks(
            config,
            batch_id="batch-1",
            model_id="fake-4x",
            output_format="PNG",
            quality=90,
            tasks=(
                QueuedTaskInput(
                    request_id="req-1",
                    input_filename="source.png",
                    input_path=input_path,
                    model_id="fake-4x",
                    output_format="PNG",
                    quality=90,
                ),
            ),
        )

    assert list_tasks(config) == []
