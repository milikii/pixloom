# Database Guidelines

> Database and persistence conventions for Pixloom.

---

## Overview

Pixloom v1.1 uses a small SQLite database for task and batch state.

Persistence ownership is split deliberately:

- `state/pixloom.sqlite3` stores mutable task queue state and batch metadata.
- `models/` stores manually installed model files.
- `input/` stores persisted uploads.
- `output/` stores generated images.
- `logs/` stores append-only JSONL request audit events.

SQLite is the source of truth for task status. JSONL remains the audit trail.
Image files remain filesystem artifacts. Do not add Postgres, Redis, an ORM, or a
second queue backend unless a future task explicitly requires it.

---

## Persistence Pattern

- Use `pathlib.Path` for all persisted paths.
- Use Python stdlib `sqlite3`; do not introduce an ORM for the current task queue.
- Keep SQLite schema and writes in `app/tasks.py`.
- Initialize the schema from `initialize_task_store(config)` at app startup and
  before direct task operations.
- Claim queued work transactionally with `BEGIN IMMEDIATE` so two workers cannot
  claim the same queued row.
- Persist uploaded files only under `input/`.
- Persist generated files only under `output/`.
- Persist request audit logs only under `logs/`.
- Resolve model files relative to `models/`.
- Store SQLite under `PIXLOOM_DB_PATH`, defaulting to `state/pixloom.sqlite3`.
- Build legacy WebUI history from successful JSONL events plus existing files
  under `output/` until the task-list UI fully replaces it.
- Delete history items only by resolving paths safely under configured `input/` and
  `output/` directories.
- Keep retention cleanup disabled by default unless an explicit positive retention
  day count is configured.

Current examples:

- `app/config.py`
- `app/inference.py`
- `app/history.py`
- `app/request_logging.py`
- `app/tasks.py`

## Task Schema Contract

Current tables:

- `batches(id, created_at, model_id, output_format, quality,
  output_size_preset, total_count)`
- `tasks(request_id, batch_id, status, input_filename, input_path, output_path,
  model_id, output_format, quality, output_size_preset, created_at, started_at,
  completed_at, elapsed_seconds, error_code, error_detail, retry_of_request_id)`

Allowed task statuses:

- `queued`
- `running`
- `completed`
- `failed`
- `deleted`
- `interrupted`

`request_id` remains the per-image trace id. `batch_id` groups related uploads,
including the one-image batch used by the current single-image flow.

`output_size_preset` must be persisted on both the batch and task rows. Allowed
values are `native`, `2k`, `4k`, and `8k`; old rows default to `native`.

---

## Scenario: SQLite Task Queue

### 1. Scope / Trigger

Use this contract whenever a feature creates, claims, lists, completes, fails,
deletes, retries, or displays queued upscale work.

### 2. Signatures

- `AppConfig.db_path: Path`
- `load_config()` reads `PIXLOOM_DB_PATH`, default `state/pixloom.sqlite3`
- `initialize_task_store(config: AppConfig) -> None`
- `create_batch(config, *, batch_id, model_id, output_format, quality, output_size_preset="native", total_count) -> BatchRecord`
- `enqueue_task(config, *, request_id, batch_id, input_filename, input_path, model_id, output_format, quality, output_size_preset="native", retry_of_request_id="") -> TaskRecord`
- `claim_next_queued_task(config) -> TaskRecord | None`
- `claim_queued_task(config, request_id: str) -> TaskRecord | None`
- `mark_task_completed(config, *, request_id, output_path, elapsed_seconds) -> TaskRecord`
- `mark_task_failed(config, *, request_id, error_code, error_detail) -> TaskRecord`
- `mark_running_tasks_interrupted(config) -> int`
- `delete_task(config, request_id: str) -> TaskDeleteResult`
- `get_task(config, request_id: str) -> TaskRecord | None`
- `list_tasks(config, *, statuses: tuple[str, ...] | None = None, limit: int | None = None) -> list[TaskRecord]`

### 3. Contracts

- A task row must reference an existing batch row.
- Task rows must carry the same output size preset requested for their batch unless
  a future retry flow deliberately overrides it.
- Uploaded files must be persisted under `input/` before enqueueing so queued work
  can survive browser disconnects.
- Claiming a task changes only `queued -> running` inside a `BEGIN IMMEDIATE`
  transaction.
- Completing or failing a task must also write a request log row:
  `task_completed` or `task_failed`.
- App startup must call `mark_running_tasks_interrupted(config)` after
  `initialize_task_store(config)`.
- Deleting a task must re-read by `request_id`, skip `running` tasks, delete only
  safe paths under configured `input/` and `output/`, mark the row `deleted`, and
  log `task_deleted`.
- JSONL logs must never be used as the mutable queue state source of truth.

### 4. Validation & Error Matrix

| Condition | Behavior | Required Test |
|---|---|---|
| DB parent missing | `initialize_task_store` creates it | `test_initialize_task_store_creates_sqlite_file` |
| No queued task | claim helper returns `None` | `test_claim_next_queued_task_is_transactional_by_status` |
| Same task claimed twice | second claim returns `None` | `test_enqueue_and_claim_task_transitions_to_running` |
| Backend succeeds | task becomes `completed` with output path and elapsed seconds | `test_mark_task_completed_records_output_and_elapsed_time` |
| Backend fails | task becomes `failed` with error fields | `test_mark_task_failed_keeps_error_fields_visible` |
| App restarts mid-task | running tasks become `interrupted` | `test_mark_running_tasks_interrupted_after_restart` |
| Delete completed task | safe input/output files are removed and row becomes `deleted` | `test_delete_task_removes_safe_input_and_output_files` |
| Delete unsafe paths | files outside runtime dirs are skipped | `test_delete_task_skips_paths_outside_runtime_directories` |

### 5. Good / Base / Bad Cases

- Good: UI persists one or more uploads, inserts one batch, enqueues one task per
  image, claims each exact `request_id`, runs inference sequentially, then marks
  each row completed or failed.
- Base: queue worker asks for the next task and receives `None` when there is no
  queued work.
- Bad: UI stores only a browser callback list and loses queued work after refresh.
- Bad: task list reconstructs mutable status from JSONL instead of SQLite.

### 6. Tests Required

- Config tests for default and env-provided `PIXLOOM_DB_PATH`.
- Task store tests for schema creation, enqueue, claim, complete, fail, interrupt,
  and filtered listing.
- UI handler tests proving the visible single-image flow writes a completed or
  failed SQLite row and keeps request logs correlated by `request_id`.
- Batch handler tests proving multiple images share one `batch_id` and one failed
  image does not abort the remaining images.
- Delete tests proving only safe runtime paths are removed.

### 7. Wrong vs Correct

#### Wrong

```python
# Claims whatever is next, even when the UI just enqueued a specific request.
task = claim_next_queued_task(config)
```

#### Correct

```python
queued = enqueue_task(config, request_id=request_id, batch_id=batch_id, ...)
task = claim_queued_task(config, queued.request_id)
```

The UI path should claim the exact task it just enqueued. A background worker may
use `claim_next_queued_task(config)` when it is intentionally processing the queue
globally.

---

## Naming Conventions

- Output files should include timestamp, source slug, model id, and scale.
- Log files should be date-partitioned JSONL files, for example
  `logs/pixloom-YYYYMMDD.jsonl`.
- The default SQLite file should stay under `state/` so Compose can mount it as
  `/data/state/pixloom.sqlite3`.
- Model filenames must match the registry entries documented in `README.md`.

---

## Migrations

The initial v1.1 schema is created automatically with `CREATE TABLE IF NOT EXISTS`.

If a future feature changes structured storage, document:

1. why the schema change is needed
2. the migration path from the current SQLite schema and runtime directories
3. the rollback plan
4. test coverage for old and new rows

Do not silently introduce a second source of truth for task state.

---

## Common Mistakes

- Adding another database or queue backend without replacing the existing contract
- Writing outputs outside `output/`
- Using ad-hoc log filenames that break chronological scanning
- Treating `models/` metadata as dynamic state instead of static installed assets
- Deleting paths from logs without first proving they are inside runtime directories
- Reconstructing current queue status from JSONL instead of SQLite
- Letting SQLite point at input/output paths outside configured runtime directories
