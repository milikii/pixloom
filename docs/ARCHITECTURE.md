# Pixloom Architecture

Last updated: 2026-05-04

## Goal

Pixloom is a self-hosted NAS image upscaling WebUI. The current release lets a
phone browser upload one image or a small batch, choose a model, understand which
model is suitable, run CPU-only upscaling sequentially, preview the output, and
download the result.

This is not a ComfyUI replacement and not a model workflow editor. The service
optimizes for a small, boring, verifiable NAS deployment.

## Runtime Shape

Production is one container and one external port:

```text
phone browser
  -> nginx on NAS host or trusted LAN client
     -> http://192.168.2.220:7860
        -> FastAPI in Docker
           -> static React/Next.js export
           -> /api routers
           -> in-process background worker
           -> model registry
           -> SQLite task queue
           -> CPU inference backend
           -> persisted input/output/log/state folders
```

Docker builds the React frontend as a static export and copies it into the Python
runtime image. FastAPI serves both the API and static frontend on `0.0.0.0:7860`.

The application does not own public HTTPS, certificates, or login. Those stay in
host nginx or another upstream authentication layer.

## Runtime Layout

```text
repo/
  Dockerfile
  compose.yml
  app/
    config.py
    history.py
    inference.py
    model_inventory.py
    model_matrix.py
    model_registry.py
    request_logging.py
    spandrel_backend.py
    tasks.py
  backend/
    requirements.txt
    pixloom_api/
    worker/
  frontend/
    src/
    package.json
    next.config.ts
  bundled-models/
  models/
  input/
  output/
  logs/
  state/
```

## File Storage And Retention

Pixloom keeps image artifacts on the filesystem and stores task state in SQLite.

- Successful uploads are persisted under `input/`.
- Successful upscaled images are persisted under `output/`.
- Task-row preview thumbnails are cached under `thumbnails/`.
- Request audit events are appended under `logs/`.
- Task and batch rows are stored under `state/pixloom.sqlite3` by default.
- Optional image-model defaults can be baked into the image under
  `bundled-models/` and copied into `models/` on startup only when the runtime
  file is missing.
- Failed requests roll back output files created by that request when possible.
- The task list is rebuilt from SQLite task rows through `/api/tasks`.
- Deleting a task deletes linked input/output files and known cached thumbnails
  when those paths are safely inside managed runtime directories, marks the row
  `deleted`, and logs `task_deleted`.
- Retention cleanup keeps the most recent 30 days of finished task files by
  default. `PIXLOOM_HISTORY_RETENTION_DAYS=0` disables task-file retention.
- Batch download archives use `pixloom-results-*.zip`, are removed after the
  response when possible, and are also swept after `PIXLOOM_ARCHIVE_TTL_HOURS`
  hours so interrupted downloads do not accumulate.
- `GET /api/storage` reports managed bytes by category and current disk usage.
- On app startup, any task left as `running` is marked `interrupted`.

SQLite is the task status source of truth. `logs/` provide request audit metadata;
`input/` and `output/` remain the source of truth for local image files.

Default Compose port binding:

```yaml
ports:
  - "7860:7860"
```

## Data Flow

```text
React upload form
  |
  v
POST /api/upload persists each original to input/
  |
  v
POST /api/batches validates selected model and creates one batch row plus one
queued task row per image, including the requested output size preset
  |
  v
BackgroundTaskWorker claims queued tasks transactionally
  |
  v
Validate format + size
  |-- invalid format/too large -> failed task + log
  |
  v
Resolve model from registry and models/
  |-- missing file/unsupported backend -> failed task + log
  |
  v
Run CPU tiled inference through Spandrel
  |-- target preset -> prepare proportional intermediate input if needed
  |-- inference error/OOM -> failed task + log
  |
  v
Final resize to requested longest side when target preset is 2K/4K/8K
  |
  v
Persist result to output/
  |
  v
Mark task completed in SQLite
  |
  v
React polls /api/tasks, displays selected previews/downloads through
/api/files/output/*, and uses cached thumbnails from /api/files/output-thumbnail/*
for task rows
```

## Task Queue Contract

Current SQLite tables:

```text
batches(id, created_at, model_id, output_format, quality,
        output_size_preset, total_count)
tasks(request_id, batch_id, status, input_filename, input_path, output_path,
      model_id, output_format, quality, output_size_preset, created_at,
      started_at, completed_at, elapsed_seconds, progress_value, progress_step,
      error_code, error_detail, retry_of_request_id)
```

Allowed task statuses are `queued`, `running`, `completed`, `failed`, `deleted`,
and `interrupted`. `request_id` remains the per-image trace id; `batch_id` groups
one or more images.

The worker is in-process with FastAPI and processes one task at a time. There is no
external Redis queue or second worker container.

`output_size_preset` is one of `native`, `2k`, `4k`, or `8k`. `native` keeps the
model's fixed scale. Target presets set the final longest side to 2048px, 4096px,
or 8192px while preserving aspect ratio. Pixloom does not crop to a 16:9 video
canvas, and output remains bounded by `PIXLOOM_MAX_OUTPUT_SIDE`.

## Backend Scope

- `spandrel` / PyTorch CPU is the implemented model backend. The Docker image
  installs PyTorch from the CPU wheel index explicitly.
- The model registry supports `spandrel`, `onnxruntime`, and `custom` backend
  entries. Unsupported future backends must stay hidden from the operator dropdown.
- No automatic downloader. Models are either shipped in the image as a bundled
  baseline pack or placed manually into `models/`.
- CPU tiled inference is required for NAS memory safety.

## API Surface

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

## Security Boundary

Application responsibilities:

- Validate image extensions and decoded image type.
- Enforce max input and output dimensions.
- Save uploads only under `input/`.
- Save outputs only under `output/`.
- Assign a request id to every upscale attempt.
- Write append-only structured JSONL logs.
- Serve files and generated thumbnails only through safe `/api/files/*` path
  resolution.
- Report storage usage only for configured managed runtime paths.
- Show Chinese-first errors without dumping secrets or full tracebacks into the UI.

Host nginx responsibilities:

- HTTPS certificate.
- Public hostname.
- Basic Auth, Authelia, OAuth2 Proxy, or existing unified login.
- Upload body size limit.
- Proxy timeout long enough for CPU inference.

## Test Plan

Use `pytest` for Python contracts and the frontend toolchain for TypeScript/Next.

Recommended automated checks:

```text
.venv/bin/pytest -q
cd frontend && npm run lint && npm run build
docker compose build
```

Primary test files:

- `tests/test_api.py`
- `tests/test_model_registry.py`
- `tests/test_inference_validation.py`
- `tests/test_output_paths.py`
- `tests/test_tasks.py`
- `tests/test_spandrel_backend.py`

Real model testing remains a documented manual acceptance test on the NAS.

## Performance Risks

- CPU inference is slow. The UI must show queued/running/completed states and not
  imply interactive speed.
- Large input images can exhaust memory. Enforce max dimensions before inference.
- Full-frame model execution can exhaust memory even if input passes validation.
  Use tiled inference by default.
- Model load time is high. Cache loaded models by model id and path metadata.
- Concurrent requests can overload NAS CPU. Keep one serial worker in the current
  release.

## NOT In Scope

- ComfyUI-style workflow graph.
- Parallel inference.
- External worker service or Redis-style queue.
- Public model downloader.
- GPU/CUDA/ROCm support.
- ncnn-vulkan acceleration.
- User account system inside the app.
- CI image publishing or registry release.
- Automatic nginx configuration.
