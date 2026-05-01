from __future__ import annotations

from pathlib import Path

from app.config import AppConfig
from app.tasks import (
    claim_next_queued_task,
    claim_queued_task,
    create_batch,
    delete_task,
    enqueue_task,
    get_task,
    initialize_task_store,
    list_tasks,
    mark_running_tasks_interrupted,
    mark_task_completed,
    mark_task_failed,
)


def _config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        input_dir=tmp_path / "input",
        output_dir=tmp_path / "output",
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
    assert claimed is not None
    assert claimed.status == "running"
    assert claimed.started_at is not None
    assert claim_queued_task(config, "req-1") is None


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
    assert not input_path.exists()
    assert not output_path.exists()
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
    assert outside_input in result.skipped_paths
    assert outside_output in result.skipped_paths
