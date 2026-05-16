# Pixloom Task Plan

Last updated: 2026-05-04

## Current Baseline

Pixloom now ships as one React/FastAPI Docker service on port `7860`.

- `Dockerfile` builds the Next.js static export and copies it into the Python image.
- `compose.yml` has one service, `pixloom`, with `7860:7860`.
- FastAPI serves `/api/*`, `/api/files/*`, and the static frontend export.
- The SQLite background worker runs in-process and claims queued tasks serially.
- Legacy Gradio deployment files and entrypoints are removed.

## Completed

1. Runtime directories and persistence.
   - `models/`, `input/`, `output/`, `logs/`, and `state/`.
   - Compose persists those directories under `/data/*`.

2. Model registry and inference.
   - Explicit model metadata and Chinese guidance fields.
   - Operator-visible models are separated from evaluation-only models.
   - Spandrel/PyTorch CPU backend with tiled inference.
   - ONNX Runtime and custom face-restoration backends are available for promoted
     APISR, CodeFormer, and GFPGAN entries.

3. Task queue.
   - SQLite `batches` and `tasks` tables.
   - Queue, claim, complete, fail, interrupt, delete, and list task records.
   - One in-process background worker processes tasks serially.

4. FastAPI API.
   - `GET /api/health`
   - `GET /api/models`
   - `POST /api/upload`
   - `POST /api/batches`
   - `GET /api/tasks`
   - `DELETE /api/tasks/{request_id}`
   - `GET /api/logs/{request_id}`
   - `GET /api/storage`
   - `GET /api/files/input/{path}`
   - `GET /api/files/output/{path}`
   - `GET /api/files/output-thumbnail/{path}`
   - `GET /api/files/output-archive`
   - `POST /api/files/output-archive`

5. React frontend.
   - Next.js SPA under `frontend/`.
   - Chinese-first submission, model guidance, task list, logs, preview, and delete
     flows.
   - Cached task-row thumbnails and zip download for selected completed tasks.
   - Storage status panel for models, uploads, outputs, thumbnails, logs, SQLite
     state, and temporary download archives.
   - Tailwind v4 semantic design tokens.
   - Static export for production deployment.

6. Output size presets.
   - `native`, `2k`, `4k`, and `8k` are accepted submission presets.
   - Target presets preserve aspect ratio by final longest side.
   - SQLite persists `output_size_preset` on both batch and task rows.
   - Task detail and JSONL logs expose the preset for historical traceability.

7. Documentation.
   - README and architecture document describe the one-container deployment.
   - Project execution guidance now points future agents at React/FastAPI rather than the removed
     Gradio entrypoint.

8. Storage lifecycle.
   - Finished task files default to 30-day retention, configurable through
     `PIXLOOM_HISTORY_RETENTION_DAYS`.
   - Manual task deletion removes linked uploads, outputs, and cached thumbnails.
   - Stale batch-download zip files are swept after `PIXLOOM_ARCHIVE_TTL_HOURS`.

## Current Verification Targets

- `.venv/bin/pytest -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `docker compose build`
- `docker compose up -d`
- `curl http://localhost:7860/api/health`
- Browser load of `http://localhost:7860`

## P1

1. Add resource telemetry: memory estimate, tile size, and per-stage timings.
2. Add a dry-run cleanup command if operators need a CLI preview before changing
   retention cleanup.

## Explicitly Deferred

- Parallel batch processing.
- GPU/CUDA/ROCm support.
- ncnn-vulkan.
- Public model downloader.
- User account system inside the app.
- Docker image publishing pipeline.
- Automatic nginx configuration.
