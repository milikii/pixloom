# Logging Guidelines

> Request-level logging and audit trail conventions for Pixloom.

---

## Overview

Pixloom uses lightweight append-only JSONL logs under `logs/`.

The logging entrypoint is `app/request_logging.py`. The backend and UI should both
log through `log_event(...)` so every request can be traced by `request_id`.

---

## Required Fields

Every log row must include:

- `timestamp`
- `request_id`
- `event`
- `status`
- `model_id`
- `input_filename`
- `input_path`
- `output_path`
- `elapsed_seconds`
- `error_code`
- `error_detail`

When known, also include:

- `input_dimensions.width`
- `input_dimensions.height`
- `output_dimensions.width`
- `output_dimensions.height`
- `output_size_preset`
- `target_longest_side`

---

## Event Types

Current lifecycle events:

- `task_queued`
- `task_completed`
- `task_failed`
- `task_deleted`
- `request_started`
- `inference_started`
- `request_succeeded`
- `request_failed`
- `ui_rejected`
- `history_deleted`
- `history_pruned`

These event names should stay explicit and boring. Do not invent vague names like
`process_event` or `task_update`.

---

## What To Log

- one row when a request starts
- one row when a task is queued in SQLite
- one row when backend inference begins
- one row when the request finishes successfully
- one row when the SQLite task is marked completed
- one row when the request fails
- one row when the SQLite task is marked failed
- one row when an operator deletes a SQLite task
- one row when the API or UI boundary rejects a request before inference starts
- one row when an operator deletes a history item
- one row when retention cleanup prunes an old history item

Examples live in:

- `app/request_logging.py`
- call sites in `app/inference.py`
- call sites in `app/history.py`
- call sites in `app/tasks.py`

---

## What Not To Log

- raw image bytes
- passwords or auth headers
- absolute user device paths
- Python tracebacks copied straight into operator-visible logs when a concise detail
  string is enough

The logs are for operational tracing, not for dumping every in-memory detail.

---

## Review Checklist

- Every user-visible failure includes a request id
- Every request id appears in `logs/`
- Success and failure paths both log
- Log rows stay valid JSONL
