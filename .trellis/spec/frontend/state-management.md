# State Management

> How UI state is handled in Pixloom today.

---

## Overview

Pixloom uses local React state for transient form selections and TanStack Query for
server data. Durable task state lives in SQLite through FastAPI endpoints, not in
the browser.

---

## State Categories

- **Startup state**: available model list from `/api/models`
- **Per-request state**: uploaded image path, chosen model id, output size preset,
  output format, quality, request id
- **Task state**: queued/running/completed/failed/deleted/interrupted rows stored
  in SQLite
- **Result state**: preview path, download path, status text
- **History state**: current thumbnail list, selected request id, derived paths from
  logs

React components may hold selected ids and form state, but durable queue status
must be re-read from FastAPI/SQLite.

---

## Rules

- Fetch model metadata through `useModels()` and compute guidance from structured
  model fields.
- Generate request id per upscale attempt, not at app startup.
- Keep request and task lifecycle state in backend functions where validation,
  SQLite updates, and logging also happen.
- Keep `output_size_preset` durable in the backend task row. The browser may own the
  current selection before submit, but task detail must display the server-returned
  value after enqueue.
- Do not trust browser-held task data for deletion or retry decisions; re-read the
  task row by request id before touching files.
- Refresh visible task state through `/api/tasks` after batch submit, refresh, or
  delete.
- Store only the selected request id in UI state for deletion; the backend must
  re-read the SQLite task row and re-resolve file paths before deleting.

## Current Examples

- `frontend/src/app/page.tsx`: owns selected files, selected model, output params,
  and selected task id.
- `frontend/src/hooks/`: wraps API calls with TanStack Query mutations/queries.
- `app/tasks.py`: `TaskRecord` rows are the durable source for task status,
  output paths, elapsed time, and error fields.
- `tests/test_tasks.py` and `tests/test_api.py`: prove task state is stored in
  SQLite and exposed through FastAPI.

---

## Common Mistakes

- introducing a global mutable cache for UI values
- keeping stale model guidance disconnected from the current dropdown value
- mixing configuration state with per-request state
- deleting files based only on stale browser state instead of backend-resolved
  history data
- showing queued/running status from stale callback output after SQLite has changed
- hiding failed tasks because they have no output thumbnail
