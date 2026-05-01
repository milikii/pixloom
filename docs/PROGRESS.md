# Pixloom Progress

Last updated: 2026-05-01

## Current Phase

Pixloom v1 is implemented. V1.1 has durable task state, multi-image sequential
batch submission, and a SQLite-backed task list. The remaining V1.1 work is model
configuration polish.

## Completed

- Product requirements captured in `nas-upscale-webui-requirements副本.md`.
- Architecture captured in `docs/ARCHITECTURE.md`.
- High-level tasks captured in `docs/TASKS.md`.
- Executable implementation plan captured in `docs/superpowers/plans/2026-04-30-pixloom-v1.md`.
- Chinese-first Gradio UI copy implemented.
- Model suitability guidance surfaced in the WebUI.
- Request-id based error contract implemented.
- JSONL request audit logging implemented under `logs/`.
- Thumbnail history implemented for successful outputs.
- History deletion removes linked local input/output images when paths are safe.
- Optional retention cleanup added and disabled by default.
- Trellis backend and frontend spec files filled based on the real codebase.
- `PIXLOOM_DB_PATH` added with default `state/pixloom.sqlite3`.
- SQLite `batches` and `tasks` tables added in `app/tasks.py`.
- Existing single-image upscale flow now enqueues, claims, completes, or fails a
  task row while preserving the current UI return shape.
- Multi-image uploads now create one batch with one task per image and process
  sequentially.
- One failed image in a batch no longer aborts the remaining images.
- The WebUI task list now reads from SQLite and shows completed, failed, deleted,
  interrupted, queued, and running statuses.
- Task deletion removes only safe linked runtime files, marks the task deleted,
  and logs `task_deleted`.
- Startup marks stale `running` tasks as `interrupted`.
- Compose persists `state/` as `/data/state`.

## Verification

- `python3 -m compileall app tests`: passed
- `.venv/bin/pytest -q tests/test_config.py tests/test_history.py tests/test_inference_validation.py tests/test_app_handler.py`: passed (`30 passed`)
- `.venv/bin/pytest -q tests/test_app_handler.py tests/test_inference_validation.py tests/test_spandrel_backend.py`: passed (`23 passed`)
- `.venv/bin/pytest -q`: passed (`49 passed`)
- `docker run --rm -v "$PWD:/workspace" -w /workspace pixloom-upscale-webui python -m pytest -q`: passed (`43 passed`)
- `docker compose build`: passed
- `docker compose up -d --force-recreate`: passed
- Container is currently publishing `0.0.0.0:7860->7860/tcp`
- 2026-05-01 V1.1 queue slice:
  - `.venv/bin/python -m compileall app tests`: passed
  - `.venv/bin/pytest -q tests/test_config.py tests/test_tasks.py tests/test_app_handler.py tests/test_inference_validation.py`: passed (`33 passed`)
  - `.venv/bin/pytest -q`: passed (`56 passed`)
- 2026-05-01 V1.1 batch/task-list slice:
  - `.venv/bin/python -m compileall app tests`: passed
  - `.venv/bin/pytest -q tests/test_tasks.py tests/test_app_handler.py`: passed (`17 passed`)
  - `.venv/bin/pytest -q`: passed (`60 passed`)
  - `docker compose build`: passed
  - `docker compose up -d --force-recreate`: passed
  - `docker exec pixloom-upscale-webui python -c "...urllib.request..."`: passed (`200`)

## Pixloom V1 Runtime Smoke Test

- `docker compose build`: passed
- `docker compose up -d --force-recreate`: passed
- LAN host port publishing: configured for `7860:7860`
- Gradio startup log: confirmed on `0.0.0.0:7860`

## Pixloom V1 Real Model Acceptance

- Date: 2026-04-30
- Input size: 1402x1122
- Model: Real-ESRGAN 4x Anime
- Output size: 5608x4488
- Elapsed time: 92.11s
- Output path: output/20260430-031033-809102_image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0_realesrgan-x4plus-anime_4x.png
- Phone browser preview: pending manual browser check
- Download: pending manual browser check
- Container restart persistence: passed for runtime directories; output file written successfully under `output/`

## Remaining Manual Checks

- Confirm the Chinese-first UI renders as expected from a real phone browser.
- Trigger one controlled failure in the WebUI and confirm the request id appears and matches a row in `logs/`.
- Confirm model guidance text is understandable on a narrow mobile viewport.
- Submit one real batch from a phone and confirm `state/pixloom.sqlite3` contains
  one batch id with multiple task rows.
- Delete one completed task from the WebUI and confirm only the linked input/output
  files are removed.
- Continue V1.1 with model recommendation polish.
