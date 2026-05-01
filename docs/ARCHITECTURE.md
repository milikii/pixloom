# Pixloom Architecture

Last updated: 2026-05-01

## Goal

Pixloom is a self-hosted NAS image upscaling WebUI. The current release lets a phone browser upload one image or a small batch, choose a model, understand which model is suitable, run CPU-only upscaling sequentially, preview the output, and download the result.

This is not a ComfyUI replacement and not a model workflow editor. The first release optimizes for a small, boring, verifiable NAS service.

V1.1 turns that flow into a task-backed NAS job console. Single-image and
multi-image submissions are recorded in SQLite while keeping the current Gradio UI
and one-at-a-time CPU inference path.

## Engineering Decision

Use the minimum service shape that can run on an x86 NAS:

```text
phone browser
  -> nginx on NAS host or trusted LAN client
     -> http://192.168.2.220:7860
        -> Gradio app in Docker
           -> model registry
           -> SQLite task queue
           -> CPU inference backend
           -> persisted input/output/log/state folders
```

The application does not own public HTTPS, certificates, or login. Those stay in host nginx. The app is published on the NAS host for trusted LAN access and can still sit behind nginx for public access.

## Runtime Layout

```text
repo/
  compose.yml
  app/
    Dockerfile
    requirements.txt
    app.py
    config.py
    history.py
    inference.py
    model_registry.py
    request_logging.py
    tasks.py
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
- Request audit events are appended under `logs/`.
- Task and batch rows are stored under `state/pixloom.sqlite3` by default.
- Failed requests roll back output files created by that request when possible.
- The WebUI task list is rebuilt from SQLite task rows.
- Completed tasks with existing output files also appear as thumbnails.
- Deleting a task deletes its linked input and output files when those paths are
  safely inside `input/` and `output/`, marks the row `deleted`, and logs
  `task_deleted`.
- Retention cleanup is disabled by default and enabled only when
  `PIXLOOM_HISTORY_RETENTION_DAYS` is set to a positive day count.
- On app startup, any task left as `running` is marked `interrupted`.

This means a successful output remains available after the browser tab closes and
after the container restarts, until the NAS operator deletes it manually. This is
intentional for the first NAS version because the user may run a slow CPU upscale
from a phone and come back later to collect the file.

SQLite is the task status source of truth. `logs/` provide request audit metadata;
`input/` and `output/` remain the source of truth for local image files.

Default Compose port binding:

```yaml
ports:
  - "7860:7860"
```

Gradio listens inside the container on `0.0.0.0:7860`. Docker publishes it on host port `7860` for trusted LAN access by default.

## Data Flow

```text
Upload one image or multiple images
  |
  v
Resolve selected model from registry
  |-- missing file/unsupported backend -> clear UI error
  |
  v
Persist each original to input/
  |
  v
Create one batch row + one queued task row per image
  |
  v
Claim each queued task transactionally
  |
  v
Validate format + size
  |-- invalid format/too large -> failed task + continue next image
  |
  v
Load cached model
  |-- first use: load from models/
  |-- later use: reuse cached descriptor/session
  |
  v
Run CPU tiled inference
  |-- inference error/OOM -> failed task + continue next image + log
  |
  v
Persist result to output/
  |
  v
Mark task completed in SQLite
  |
  v
Return batch summary + first completed preview/download + task list refresh
```

## Task Queue Contract

Current SQLite tables:

```text
batches(id, created_at, model_id, output_format, quality, total_count)
tasks(request_id, batch_id, status, input_filename, input_path, output_path,
      model_id, output_format, quality, created_at, started_at, completed_at,
      elapsed_seconds, error_code, error_detail, retry_of_request_id)
```

Allowed task statuses are `queued`, `running`, `completed`, `failed`, `deleted`,
and `interrupted`. `request_id` remains the per-image trace id; `batch_id` groups
one or more images.

The Gradio handler still runs in-process and sequentially. This is intentionally
not an external worker service; it gives the operator durable task rows and clear
batch status without changing the NAS deployment topology.

## Backend Scope

First implementation should include:

- `spandrel` / PyTorch CPU as the first real model backend.
- A model registry that can describe future `onnxruntime` and `realesrgan` entries without implementing every backend now.
- Manual model placement in `models/` for v1. No automatic downloader in the first pass.
- CPU tiled inference from the start, with configurable tile size and overlap.

Rationale:

- Spandrel matches the `.pth` / `.safetensors` model ecosystem better than starting with ONNX only.
- ONNX Runtime CPU is a good later backend, but it requires ONNX model availability and per-model tensor conventions.
- A downloader adds URL churn, license ambiguity, and failure modes that do not block the first usable NAS service.
- Full-frame CPU inference can run out of memory on NAS hardware; tiling is part of the first usable version, not polish.

## Model Registry Contract

Each model entry should be explicit:

```text
id
display_name
display_name_zh
backend
architecture
scale
path
image_types
notes
recommended_for_zh
warning_zh
enabled
```

The UI should show only enabled models whose files exist. Missing model files should produce a readable warning in the UI or README, not a stack trace. Model guidance should be visible in the UI before inference begins, not hidden in source metadata.

## Security Boundary

Application responsibilities:

- Validate image extensions and decoded image type.
- Enforce max input and output dimensions.
- Save uploads only under `input/`.
- Save outputs only under `output/`.
- Assign a request id to every upscale attempt.
- Write append-only structured JSONL logs under `logs/` for request start, validation failure, backend failure, and output success.
- Avoid exposing `input/` and `output/` as a public static directory.
- Show clear Chinese-first errors without dumping secrets or full tracebacks into the UI.
- Include the request id in user-visible failure output so support and logs can be correlated.

Host nginx responsibilities:

- HTTPS certificate.
- Public hostname.
- Basic Auth, Authelia, OAuth2 Proxy, or existing unified login.
- Upload body size limit.
- Proxy timeout long enough for CPU inference.
- WebSocket/streaming-safe proxy headers if Gradio needs them.

## Test Plan

Use `pytest` with unit tests for pure logic and lightweight integration tests that
do not require real model downloads.

```text
CODE PATHS                                      USER FLOWS
[+] app/model_registry.py                       [+] Phone upload flow
  ├── [GAP] list enabled models                   ├── [GAP] upload valid image
  ├── [GAP] hide missing model files              ├── [GAP] choose model
  └── [GAP] reject unknown model id               ├── [GAP] run upscale
                                                  └── [GAP] download output

[+] app/inference.py                            [+] Error states
  ├── [GAP] validate image format                 ├── [GAP] unsupported file
  ├── [GAP] enforce max input size                ├── [GAP] too-large image
  ├── [GAP] generate safe output filename         ├── [GAP] missing model file
  ├── [GAP] cache loaded model                    └── [GAP] backend failure
  ├── [GAP] tiled inference path
  └── [GAP] backend exception path

[+] app/app.py
  ├── [GAP] Gradio handler returns preview/file/status
  ├── [GAP] batch handler groups multiple images under one batch id
  ├── [GAP] one failed batch image does not abort the rest
  ├── [GAP] handler maps known errors to UI messages
  └── [GAP] auth env vars optional, not required

[+] app/tasks.py
  ├── [GAP] initialize SQLite schema
  ├── [GAP] enqueue and claim queued tasks transactionally
  ├── [GAP] mark completed/failed/interrupted tasks
  ├── [GAP] delete tasks and remove only safe runtime paths
  └── [GAP] filter task lists by status

COVERAGE TARGET: all planned branches covered before ship.
```

Recommended test files:

- `tests/test_model_registry.py`
- `tests/test_inference_validation.py`
- `tests/test_output_paths.py`
- `tests/test_app_handler.py`
- `tests/test_tasks.py`

Use a fake backend in tests so CI/local tests do not need large model files. Real model testing should be a documented manual acceptance test on the NAS.

## Performance Risks

- CPU inference is slow. The UI must show elapsed time and not imply interactive speed.
- Large input images can exhaust memory. Enforce max dimensions before inference.
- Full-frame model execution can exhaust memory even if the input passes validation. Use tiled inference by default.
- Model load time is high. Cache loaded models by model id and path metadata.
- Concurrent requests can overload NAS CPU. Keep Gradio concurrency low for v1,
  ideally one inference at a time. Batch processing is sequential and multiplies
  total elapsed time.

## UX And Error Contract

- Primary operator-facing UI copy should be Chinese-first.
- Error handling should use a small explicit contract:
  - error_code
  - user_message_zh
  - likely_cause_zh
  - suggested_action_zh
  - request_id
- Validation, missing-model, backend, and output-write failures should map to distinct messages.

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

## Current V1.1 Split

- Done in the first slice: SQLite task/batch schema, single-image enqueue/claim,
  task completion/failure recording, restart interruption marking, and runtime
  `state/` persistence.
- Next slice: multi-image upload, visible task list, deletion from task rows, and
  broader model configuration.

## Parallelization

Sequential implementation is recommended for v1. The same small set of modules (`app/`, `compose.yml`, README) is touched by every step, so parallel worktrees would create more coordination than speed.

## Source Notes

- Gradio supports `server_name`, `server_port`, and optional `auth` on `Blocks.launch`.
- Docker Compose `ports` supports host IP binding; omitting host IP binds to all interfaces.
- ONNX Runtime has a CPU Python package and `InferenceSession` execution providers.
- Spandrel loads PyTorch super-resolution models and supports many SR architectures, but its README states it does not yet provide complete easy inference code.
