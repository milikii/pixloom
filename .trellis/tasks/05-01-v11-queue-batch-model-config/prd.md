# Pixloom V1.1 Task Queue, Batch Upload, And Model Configuration

## Goal

Turn Pixloom from a single-image upscaler with thumbnail history into a small NAS job console: the operator can submit one or more images, see queued/running/completed/failed work, return later from a phone, and choose models that fit the CPU-only hardware.

## What I Already Know

- Pixloom v1 currently supports one uploaded image per run through Gradio.
- `demo.queue(default_concurrency_limit=1)` already serializes inference work.
- Successful outputs are currently rebuilt from append-only JSONL logs and existing files under `output/`.
- Request ids already exist and should remain the per-image trace id.
- Current planned V1.1 design is captured in `docs/superpowers/plans/2026-05-01-pixloom-queue-batch-models.md`.
- The NAS target remains CPU-only, so parallel inference is out of scope by default.

## Assumptions

- Use Python stdlib `sqlite3`; do not add an ORM.
- Keep JSONL request logs as the append-only audit trail.
- SQLite becomes the task list and queue source of truth for V1.1.
- Keep Gradio as the UI layer.
- Keep one concurrent inference worker by default.
- Keep public auth outside the app; the new `pix.19970626.xyz` nginx entry handles remote login.

## Requirements

- Add `PIXLOOM_DB_PATH` configuration for a small SQLite database.
- Add durable task and batch records for queued/running/completed/failed/deleted/interrupted work.
- Preserve `request_id` as the per-image trace id and add `batch_id` for grouped uploads.
- Add a single-worker queue path that claims queued rows transactionally.
- Support single-image submission through the new queue without regressing the existing flow.
- Add multi-image batch submission with sequential CPU processing.
- Replace or evolve the history view into a task list that shows active and completed work.
- Keep failed tasks visible with Chinese error summary and request id.
- Keep deletion safe: remove linked input/output files only when they are under configured runtime directories.
- Extend model guidance/configuration so CPU-suitable model choices are clearer.

## Acceptance Criteria

- [x] A single uploaded image can be submitted as a queued task and later appears as completed or failed.
- [x] Multiple uploaded images can be submitted as one batch, with one `batch_id` and per-image `request_id`s.
- [x] One failed image does not abort the rest of the batch.
- [x] Queued/running/completed/failed/deleted/interrupted statuses are visible in the task list.
- [x] A stale running task after restart is visible as interrupted.
- [x] Successful tasks provide preview/download when the output file still exists.
- [x] Failed tasks show Chinese error code/message/next-step information.
- [x] Deleting a task removes only safe local input/output paths and logs the deletion.
- [x] JSONL request logging remains append-only and correlated by request id.
- [x] Tests cover SQLite task state, queue claim behavior, batch grouping, UI handler return shape, failure visibility, deletion safety, and restart handling.

## Definition Of Done

- Targeted pytest suites pass.
- Full pytest suite passes.
- README and architecture docs describe the task queue, DB path, and retention behavior.
- `.trellis/spec/backend/` and `.trellis/spec/frontend/` are updated for new SQLite/task-list patterns.
- Manual NAS acceptance checklist is updated for single task, batch task, failed task, and remote phone return-later flow.

## Out Of Scope

- Parallel inference.
- External worker service or Redis-style queue.
- Resumable uploads.
- Automatic model downloader.
- NCNN backend.
- Face restoration pipeline.
- Video upscaling.
- User accounts inside Pixloom.
- Changing public auth beyond the already configured nginx Basic Auth entry.

## Technical Notes

- Primary plan: `docs/superpowers/plans/2026-05-01-pixloom-queue-batch-models.md`
- Likely backend files: `app/config.py`, `app/inference.py`, `app/history.py`, new `app/tasks.py`
- Likely UI file: `app/app.py`
- Likely tests: `tests/test_config.py`, `tests/test_history.py`, new task/queue tests, `tests/test_app_handler.py`
- Current cross-layer flow to preserve:
  - UI submits work.
  - Backend validates/persists input.
  - Inference emits request lifecycle logs.
  - UI shows Chinese status/errors with request id.

## Open Questions

- Resolved 2026-05-01: split V1.1 into durable single-image task queue first, then multi-image batch UI / visible task list / model configuration polish.
