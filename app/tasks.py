from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.config import AppConfig
from app.output_size import (
    NATIVE_OUTPUT_SIZE_PRESET,
    normalize_output_size_preset,
)
from app.request_logging import log_event


TASK_STATUSES = {
    "queued",
    "running",
    "completed",
    "failed",
    "deleted",
    "interrupted",
}


@dataclass(frozen=True)
class BatchRecord:
    id: str
    created_at: datetime
    model_id: str
    output_format: str
    quality: int
    output_size_preset: str
    total_count: int


@dataclass(frozen=True)
class TaskRecord:
    request_id: str
    batch_id: str
    status: str
    input_filename: str
    input_path: Path
    output_path: Path | None
    model_id: str
    output_format: str
    quality: int
    output_size_preset: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    elapsed_seconds: float | None
    progress_value: float
    progress_step: str
    error_code: str
    error_detail: str
    retry_of_request_id: str


@dataclass(frozen=True)
class TaskDeleteResult:
    request_id: str
    deleted_paths: tuple[Path, ...]
    missing_paths: tuple[Path, ...]
    skipped_paths: tuple[Path, ...]
    message_zh: str


@dataclass(frozen=True)
class QueuedTaskInput:
    request_id: str
    input_filename: str
    input_path: Path
    model_id: str
    output_format: str
    quality: int
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET
    retry_of_request_id: str = ""


def build_batch_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"batch-{timestamp}-{uuid4().hex[:8]}"


def initialize_task_store(config: AppConfig) -> None:
    config.db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(config) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS batches (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                model_id TEXT NOT NULL,
                output_format TEXT NOT NULL,
                quality INTEGER NOT NULL,
                output_size_preset TEXT NOT NULL DEFAULT 'native',
                total_count INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                request_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_filename TEXT NOT NULL,
                input_path TEXT NOT NULL,
                output_path TEXT NOT NULL DEFAULT '',
                model_id TEXT NOT NULL,
                output_format TEXT NOT NULL,
                quality INTEGER NOT NULL,
                output_size_preset TEXT NOT NULL DEFAULT 'native',
                created_at TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL DEFAULT '',
                elapsed_seconds REAL,
                progress_value REAL NOT NULL DEFAULT 0,
                progress_step TEXT NOT NULL DEFAULT '',
                error_code TEXT NOT NULL DEFAULT '',
                error_detail TEXT NOT NULL DEFAULT '',
                retry_of_request_id TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (batch_id) REFERENCES batches(id)
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status_created
                ON tasks(status, created_at);
            """
        )
        _ensure_column(
            connection,
            "tasks",
            "progress_value",
            "ALTER TABLE tasks ADD COLUMN progress_value REAL NOT NULL DEFAULT 0",
        )
        _ensure_column(
            connection,
            "tasks",
            "progress_step",
            "ALTER TABLE tasks ADD COLUMN progress_step TEXT NOT NULL DEFAULT ''",
        )
        _ensure_column(
            connection,
            "batches",
            "output_size_preset",
            "ALTER TABLE batches ADD COLUMN output_size_preset TEXT NOT NULL DEFAULT 'native'",
        )
        _ensure_column(
            connection,
            "tasks",
            "output_size_preset",
            "ALTER TABLE tasks ADD COLUMN output_size_preset TEXT NOT NULL DEFAULT 'native'",
        )


def create_batch(
    config: AppConfig,
    *,
    batch_id: str,
    model_id: str,
    output_format: str,
    quality: int,
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET,
    total_count: int,
) -> BatchRecord:
    initialize_task_store(config)
    created_at = _now()
    preset = normalize_output_size_preset(output_size_preset)
    with _connect(config) as connection:
        connection.execute(
            """
            INSERT INTO batches (
                id, created_at, model_id, output_format, quality,
                output_size_preset, total_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                created_at,
                model_id,
                output_format,
                int(quality),
                preset,
                total_count,
            ),
        )
    return BatchRecord(
        id=batch_id,
        created_at=_parse_timestamp(created_at),
        model_id=model_id,
        output_format=output_format,
        quality=int(quality),
        output_size_preset=preset,
        total_count=total_count,
    )


def enqueue_task(
    config: AppConfig,
    *,
    request_id: str,
    batch_id: str,
    input_filename: str,
    input_path: Path,
    model_id: str,
    output_format: str,
    quality: int,
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET,
    retry_of_request_id: str = "",
) -> TaskRecord:
    initialize_task_store(config)
    created_at = _now()
    preset = normalize_output_size_preset(output_size_preset)
    with _connect(config) as connection:
        connection.execute(
            """
            INSERT INTO tasks (
                request_id, batch_id, status, input_filename, input_path,
                model_id, output_format, quality, output_size_preset,
                created_at, retry_of_request_id
            ) VALUES (?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                batch_id,
                input_filename,
                str(input_path),
                model_id,
                output_format,
                int(quality),
                preset,
                created_at,
                retry_of_request_id,
            ),
        )
    log_event(
        config,
        request_id=request_id,
        event="task_queued",
        status="queued",
        model_id=model_id,
        input_filename=input_filename,
        input_path=input_path,
        output_size_preset=preset,
    )
    task = get_task(config, request_id)
    if task is None:
        raise RuntimeError(f"Queued task not found: {request_id}")
    return task


def create_batch_with_tasks(
    config: AppConfig,
    *,
    batch_id: str,
    model_id: str,
    output_format: str,
    quality: int,
    output_size_preset: str = NATIVE_OUTPUT_SIZE_PRESET,
    tasks: tuple[QueuedTaskInput, ...],
) -> tuple[TaskRecord, ...]:
    initialize_task_store(config)
    batch_created_at = _now()
    task_created_at = _now()
    preset = normalize_output_size_preset(output_size_preset)

    with _connect(config) as connection:
        connection.isolation_level = None
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO batches (
                    id, created_at, model_id, output_format, quality,
                    output_size_preset, total_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    batch_created_at,
                    model_id,
                    output_format,
                    int(quality),
                    preset,
                    len(tasks),
                ),
            )
            for task in tasks:
                task_preset = normalize_output_size_preset(task.output_size_preset)
                connection.execute(
                    """
                    INSERT INTO tasks (
                        request_id, batch_id, status, input_filename, input_path,
                        model_id, output_format, quality, output_size_preset,
                        created_at, retry_of_request_id
                    ) VALUES (?, ?, 'queued', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task.request_id,
                        batch_id,
                        task.input_filename,
                        str(task.input_path),
                        task.model_id,
                        task.output_format,
                        int(task.quality),
                        task_preset,
                        task_created_at,
                        task.retry_of_request_id,
                    ),
                )
            connection.execute("COMMIT")
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise

    records = []
    try:
        for task in tasks:
            log_event(
                config,
                request_id=task.request_id,
                event="task_queued",
                status="queued",
                model_id=task.model_id,
                input_filename=task.input_filename,
                input_path=task.input_path,
                output_size_preset=normalize_output_size_preset(task.output_size_preset),
            )
            record = get_task(config, task.request_id)
            if record is None:
                raise RuntimeError(f"Queued task not found: {task.request_id}")
            records.append(record)
    except Exception:
        with _connect(config) as connection:
            connection.execute(
                "DELETE FROM tasks WHERE batch_id = ?",
                (batch_id,),
            )
            connection.execute(
                "DELETE FROM batches WHERE id = ?",
                (batch_id,),
            )
        raise
    return tuple(records)


def claim_next_queued_task(config: AppConfig) -> TaskRecord | None:
    return _claim_queued_task(config)


def claim_queued_task(config: AppConfig, request_id: str) -> TaskRecord | None:
    return _claim_queued_task(config, request_id=request_id)


def _claim_queued_task(
    config: AppConfig,
    request_id: str | None = None,
) -> TaskRecord | None:
    initialize_task_store(config)
    connection = _connect(config)
    claimed_request_id: str | None = None
    try:
        connection.isolation_level = None
        connection.execute("BEGIN IMMEDIATE")
        if request_id is None:
            row = connection.execute(
                """
                SELECT * FROM tasks
                WHERE status = 'queued'
                ORDER BY created_at ASC
                LIMIT 1
                """
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT * FROM tasks
                WHERE request_id = ? AND status = 'queued'
                LIMIT 1
                """,
                (request_id,),
            ).fetchone()
        if row is None:
            connection.execute("COMMIT")
            return None

        started_at = _now()
        claimed_request_id = row["request_id"]
        connection.execute(
            """
            UPDATE tasks
            SET status = 'running',
                started_at = ?,
                progress_value = 0.02,
                progress_step = '任务已开始'
            WHERE request_id = ? AND status = 'queued'
            """,
            (started_at, claimed_request_id),
        )
        connection.execute("COMMIT")
    except Exception:
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        connection.close()
    if claimed_request_id is None:
        return None
    return get_task(config, claimed_request_id)


def mark_task_completed(
    config: AppConfig,
    *,
    request_id: str,
    output_path: Path,
    elapsed_seconds: float,
) -> TaskRecord:
    task = _update_finished_task(
        config,
        request_id=request_id,
        status="completed",
        output_path=output_path,
        elapsed_seconds=elapsed_seconds,
        progress_value=1.0,
        progress_step="处理完成",
    )
    log_event(
        config,
        request_id=request_id,
        event="task_completed",
        status="completed",
        model_id=task.model_id,
        input_filename=task.input_filename,
        input_path=task.input_path,
        output_path=task.output_path,
        elapsed_seconds=task.elapsed_seconds,
        output_size_preset=task.output_size_preset,
    )
    return task


def mark_task_failed(
    config: AppConfig,
    *,
    request_id: str,
    error_code: str,
    error_detail: str,
) -> TaskRecord:
    task = _update_finished_task(
        config,
        request_id=request_id,
        status="failed",
        progress_step="处理失败",
        error_code=error_code,
        error_detail=error_detail,
    )
    log_event(
        config,
        request_id=request_id,
        event="task_failed",
        status="failed",
        model_id=task.model_id,
        input_filename=task.input_filename,
        input_path=task.input_path,
        error_code=task.error_code,
        error_detail=task.error_detail,
        output_size_preset=task.output_size_preset,
    )
    return task


def mark_running_tasks_interrupted(config: AppConfig) -> int:
    initialize_task_store(config)
    completed_at = _now()
    with _connect(config) as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET status = 'interrupted',
                completed_at = ?,
                progress_step = '任务中断',
                error_code = 'TASK_INTERRUPTED',
                error_detail = 'Task was running when the app restarted.'
            WHERE status = 'running'
            """,
            (completed_at,),
        )
        return cursor.rowcount


def delete_task(config: AppConfig, request_id: str) -> TaskDeleteResult:
    task = get_task(config, request_id)
    if task is None:
        return TaskDeleteResult(
            request_id=request_id,
            deleted_paths=(),
            missing_paths=(),
            skipped_paths=(),
            message_zh="没有找到可删除的任务，可能已经被删除或数据库记录不存在。",
        )
    if task.status == "running":
        return TaskDeleteResult(
            request_id=request_id,
            deleted_paths=(),
            missing_paths=(),
            skipped_paths=(),
            message_zh="任务正在处理，不能删除。请等待完成或失败后再删除。",
        )
    if task.status == "deleted":
        return TaskDeleteResult(
            request_id=request_id,
            deleted_paths=(),
            missing_paths=(),
            skipped_paths=(),
            message_zh=f"任务已是删除状态：{request_id}",
        )

    deleted_paths: list[Path] = []
    missing_paths: list[Path] = []
    skipped_paths: list[Path] = []
    for raw_path, root in (
        (task.input_path, config.input_dir),
        (task.output_path, config.output_dir),
    ):
        if raw_path is None:
            continue
        safe_path = _safe_runtime_child(raw_path, root)
        if safe_path is None:
            skipped_paths.append(raw_path)
            continue
        try:
            safe_path.unlink()
        except FileNotFoundError:
            missing_paths.append(safe_path)
        else:
            deleted_paths.append(safe_path)

    completed_at = _now()
    with _connect(config) as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = 'deleted',
                completed_at = ?
            WHERE request_id = ?
            """,
            (completed_at, request_id),
        )

    log_event(
        config,
        request_id=task.request_id,
        event="task_deleted",
        status="deleted",
        model_id=task.model_id,
        input_filename=task.input_filename,
        input_path=task.input_path,
        output_path=task.output_path,
        output_size_preset=task.output_size_preset,
    )

    deleted_text = "\n".join(str(path) for path in deleted_paths) or "没有实际删除文件。"
    return TaskDeleteResult(
        request_id=request_id,
        deleted_paths=tuple(deleted_paths),
        missing_paths=tuple(missing_paths),
        skipped_paths=tuple(skipped_paths),
        message_zh=f"已删除任务：{request_id}\n删除文件：\n{deleted_text}",
    )


def get_task(config: AppConfig, request_id: str) -> TaskRecord | None:
    initialize_task_store(config)
    with _connect(config) as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE request_id = ?",
            (request_id,),
        ).fetchone()
    if row is None:
        return None
    return _task_from_row(row)


def list_tasks(
    config: AppConfig,
    *,
    statuses: tuple[str, ...] | None = None,
    limit: int | None = None,
) -> list[TaskRecord]:
    initialize_task_store(config)
    query = "SELECT * FROM tasks"
    params: list[object] = []
    if statuses:
        placeholders = ", ".join("?" for _ in statuses)
        query += f" WHERE status IN ({placeholders})"
        params.extend(statuses)
    query += " ORDER BY created_at DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with _connect(config) as connection:
        rows = connection.execute(query, params).fetchall()
    return [_task_from_row(row) for row in rows]


def update_task_progress(
    config: AppConfig,
    *,
    request_id: str,
    progress_value: float,
    progress_step: str,
) -> TaskRecord:
    initialize_task_store(config)
    normalized_value = max(0.0, min(1.0, float(progress_value)))
    with _connect(config) as connection:
        connection.execute(
            """
            UPDATE tasks
            SET progress_value = ?,
                progress_step = ?
            WHERE request_id = ?
            """,
            (
                normalized_value,
                progress_step,
                request_id,
            ),
        )
    task = get_task(config, request_id)
    if task is None:
        raise RuntimeError(f"Task not found: {request_id}")
    return task


def _connect(config: AppConfig) -> sqlite3.Connection:
    connection = sqlite3.connect(config.db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _safe_runtime_child(path: Path, root: Path) -> Path | None:
    root_resolved = root.resolve(strict=False)
    path_resolved = path.resolve(strict=False)
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError:
        return None
    return path_resolved


def _update_finished_task(
    config: AppConfig,
    *,
    request_id: str,
    status: str,
    output_path: Path | None = None,
    elapsed_seconds: float | None = None,
    progress_value: float | None = None,
    progress_step: str | None = None,
    error_code: str = "",
    error_detail: str = "",
) -> TaskRecord:
    if status not in TASK_STATUSES:
        raise ValueError(f"Unknown task status: {status}")

    initialize_task_store(config)
    completed_at = _now()
    with _connect(config) as connection:
        connection.execute(
            """
            UPDATE tasks
            SET status = ?,
                completed_at = ?,
                output_path = COALESCE(NULLIF(?, ''), output_path),
                elapsed_seconds = ?,
                progress_value = COALESCE(?, progress_value),
                progress_step = COALESCE(?, progress_step),
                error_code = ?,
                error_detail = ?
            WHERE request_id = ?
            """,
            (
                status,
                completed_at,
                str(output_path) if output_path else "",
                elapsed_seconds,
                progress_value,
                progress_step,
                error_code,
                error_detail,
                request_id,
            ),
        )
    task = get_task(config, request_id)
    if task is None:
        raise RuntimeError(f"Task not found: {request_id}")
    return task


def _task_from_row(row: sqlite3.Row) -> TaskRecord:
    output_path = row["output_path"]
    return TaskRecord(
        request_id=row["request_id"],
        batch_id=row["batch_id"],
        status=row["status"],
        input_filename=row["input_filename"],
        input_path=Path(row["input_path"]),
        output_path=Path(output_path) if output_path else None,
        model_id=row["model_id"],
        output_format=row["output_format"],
        quality=int(row["quality"]),
        output_size_preset=row["output_size_preset"] or NATIVE_OUTPUT_SIZE_PRESET,
        created_at=_parse_timestamp(row["created_at"]),
        started_at=_parse_optional_timestamp(row["started_at"]),
        completed_at=_parse_optional_timestamp(row["completed_at"]),
        elapsed_seconds=(
            float(row["elapsed_seconds"]) if row["elapsed_seconds"] is not None else None
        ),
        progress_value=float(row["progress_value"] or 0),
        progress_step=row["progress_step"],
        error_code=row["error_code"],
        error_detail=row["error_detail"],
        retry_of_request_id=row["retry_of_request_id"],
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_optional_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    return _parse_timestamp(value)


def _ensure_column(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    alter_sql: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(alter_sql)


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
