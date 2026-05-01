# State Management

> How UI state is handled in Pixloom today.

---

## Overview

Pixloom uses local Gradio component state plus immutable runtime config loaded at
startup. Durable task state lives in SQLite through backend helpers, not in the
browser.

There is no Redux, Zustand, React context, or browser cache layer.

---

## State Categories

- **Startup state**: `AppConfig`, available model list
- **Per-request state**: uploaded image path, chosen model id, output format,
  quality, request id
- **Task state**: queued/running/completed/failed/deleted/interrupted rows stored
  in SQLite
- **Result state**: preview path, download path, status text
- **History state**: current thumbnail list, selected request id, derived paths from
  logs

Gradio callbacks may pass current component values and selected ids, but durable
queue status must be re-read from backend storage.

---

## Rules

- Load config once in `build_demo()`.
- Compute model guidance from the current selected model id.
- Generate request id per upscale attempt, not at app startup.
- Keep request and task lifecycle state in backend functions where validation,
  SQLite updates, and logging also happen.
- Do not trust browser-held task data for deletion or retry decisions; re-read the
  task row by request id before touching files.
- Rebuild history state from `app/history.py` after an upscale, refresh, delete, or
  retention cleanup.
- Rebuild visible task state from `app/tasks.py` after batch submit, refresh, or
  delete.
- Store only the selected request id in UI state for deletion; re-read the SQLite
  task row and re-resolve file paths on the backend before deleting.

## Current Examples

- `app/app.py`: `build_demo()` loads `runtime_config`, initializes task storage,
  marks interrupted work, and builds initial task/gallery state from
  `list_tasks(...)`.
- `app/app.py`: `task_values()` is the single refresh point for gallery entries,
  serialized state, task list text, dropdown choices, and summary text after
  submit, refresh, or delete.
- `app/tasks.py`: `TaskRecord` rows are the durable source for task status,
  output paths, elapsed time, and error fields.
- `tests/test_tasks.py` and `tests/test_app_handler.py`: prove task state is
  stored in SQLite, refreshed through backend helpers, and visible after success
  or failure.

---

## Common Mistakes

- introducing a global mutable cache for UI values
- keeping stale model guidance disconnected from the current dropdown value
- mixing configuration state with per-request state
- deleting files based only on stale browser state instead of backend-resolved
  history data
- showing queued/running status from stale callback output after SQLite has changed
- hiding failed tasks because they have no output thumbnail
