# Pixloom

Pixloom is a self-hosted NAS image upscaling WebUI. It runs as a small Docker Compose service with CPU-only inference.

The current v1 release uses a Gradio interface. A v2 React SPA + FastAPI backend is under development in `frontend/` and `backend/`.

The current release is intentionally narrow:

- upload one image or a small batch
- choose an installed model
- run CPU upscaling sequentially
- preview the output
- download the result

Pixloom is not a ComfyUI replacement and does not expose a workflow graph.

Current operator-facing behavior:

- the main WebUI copy is Chinese-first
- the model selector shows suitability guidance before inference starts
- every upscale run gets a request id
- single-image and batch runs are recorded in a SQLite task queue
- the task list shows queued, running, completed, failed, deleted, and interrupted work
- failures show operator guidance instead of a raw traceback
- request events are appended as JSONL under `logs/`
- a FastAPI backend (`backend/`) serves the same task/upload/model contracts for the v2 SPA
- a React/Next.js SPA (`frontend/`) is under development with Gallery White design system

## Directory Layout

```text
.
├── compose.yml
├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   ├── config.py
│   ├── history.py
│   ├── inference.py
│   ├── model_inventory.py
│   ├── model_matrix.py
│   ├── model_registry.py
│   ├── request_logging.py
│   ├── tasks.py
│   └── spandrel_backend.py
├── backend/
│   ├── requirements.txt
│   ├── pixloom_api/
│   │   ├── main.py
│   │   ├── deps.py
│   │   └── routers/
│   │       ├── batches.py
│   │       ├── files.py
│   │       ├── health.py
│   │       ├── logs.py
│   │       ├── models.py
│   │       ├── tasks.py
│   │       └── upload.py
│   ├── worker/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── i18n/
│   │   ├── lib/
│   │   └── providers/
│   ├── package.json
│   └── next.config.ts
├── models/
├── input/
├── output/
├── logs/
└── state/
```

Runtime data is persisted in:

- `models/`: model files placed manually
- `input/`: uploaded source images
- `output/`: generated upscaled images
- `logs/`: JSONL request audit trail
- `state/`: SQLite task queue database

## Task Queue State

Pixloom records each submitted image as a task in SQLite. The default database path
is `state/pixloom.sqlite3`; Compose mounts it as `/data/state/pixloom.sqlite3`.

Current task statuses are:

```text
queued
running
completed
failed
deleted
interrupted
```

`request_id` remains the per-image trace id used in the WebUI and JSONL logs.
`batch_id` groups related uploads. A single-image submission creates a one-item
batch; a multi-image submission creates one batch with one task per image.

On app startup, any task left as `running` is marked `interrupted` so a restart does
not leave invisible in-progress work.

Deleting a task removes only linked files that are safely under the configured
`input/` and `output/` directories, marks the SQLite row as `deleted`, and appends
a `task_deleted` audit event. Running tasks cannot be deleted.

## Model Files

Pixloom v1 does not download models automatically. Place model files in `models/` with these names:

```text
models/RealESRGAN_x4plus.pth
models/RealESRGAN_x4plus_anime_6B.pth
models/realesr-general-x4v3.pth
models/4x-UltraSharp.pth
models/4x_foolhardy_Remacri.pth
models/HAT-L-4x.pth
models/up3x-latest-denoise3x.pth
```

Only models that are both locally present and marked for operator exposure appear in
the primary WebUI dropdown. Downloaded-but-unapproved evaluation models may exist on
disk without being shown in the default submission flow.

Recommended operator choices:

- `照片自然 - 4x Remacri`: default candidate for real photos and portraits after
  the model file is locally accepted.
- `照片通用 - Real-ESRGAN 4x`: stable official photo baseline.
- `锐化插画 - 4x UltraSharp`: sharp style for AI images, compressed web images,
  and crisp illustrations.
- `动漫插画 - Real-ESRGAN Anime 6B`: anime, illustration, line art, and flat-color
  images.
- `快速试跑 - Real-ESRGAN General v3`: quick smoke tests for upload, queue, and
  output path behavior.
- `质量上限 - HAT-L 4x`: slow CPU path for small batches when detail ceiling matters
  more than latency.
- `动漫修复 - Real-CUGAN 3x 去噪`: anime/manga-focused 3x denoise option for
  compressed line art and animation frames.

Current runtime exposure rule:

- `照片自然 - 4x Remacri`
- `照片通用 - Real-ESRGAN 4x`
- `锐化插画 - 4x UltraSharp`
- `动漫插画 - Real-ESRGAN Anime 6B`
- `快速试跑 - Real-ESRGAN General v3`
- `质量上限 - HAT-L 4x`
- `动漫修复 - Real-CUGAN 3x 去噪`

Additional downloaded models remain in the local evaluation pool until they are
explicitly promoted. If local model files exist but none are yet accepted for daily
use, the UI shows a Chinese-first message explaining that the models are present but
not yet opened to normal operators.

The current FastAPI worker only implements the Spandrel backend. ONNX/custom
weights such as APISR, CodeFormer, and GFPGAN may be installed locally for
evaluation, but they stay hidden from the primary dropdown until their backend paths
are implemented.

The model guidance panel shows best fit, style, CPU speed class, local acceptance
status, and a warning before the operator submits a task.

## Start

```bash
docker compose up -d --build
```

Open the app from another device on the same LAN, or locally on the NAS:

```text
http://192.168.2.220:7860
```

The default Compose file publishes the port on the NAS host:

```yaml
ports:
  - "7860:7860"
```

This is suitable for trusted LAN access. Do not expose this port directly to the public internet.

## Stop

```bash
docker compose down
```

## Rebuild After Code Changes

```bash
docker compose build
docker compose up -d
```

## View Logs

```bash
docker compose logs -f --tail=120 upscale-webui
```

Request-level audit logs are written under `logs/` as JSONL files. When a run fails,
the WebUI shows a request id that can be matched against those files.

## Task List And File Retention

Successful runs are kept on disk:

- uploaded source images are saved under `input/`
- upscaled results are saved under `output/`
- request logs are appended under `logs/`

The WebUI now submits into a background SQLite-backed worker. The main screen is
styled as a compact operator console, and the right column is split into `结果`,
`任务`, and `日志` tabs so the operator does not have to scroll a single long
sidebar. The task tab auto-refreshes every few seconds from SQLite, keeps task
detail in one accordion, and collapses completed thumbnails by default. Selecting a
task restores its details, output preview/download when available, and request log
excerpt. Deleting a task removes the linked input and output files from local
storage when those paths are safe runtime paths. Logs remain append-only for audit
and request-id lookup.

Running tasks now persist progress stage and percentage into SQLite. The selected
task view estimates remaining time from the current progress fraction and refreshes
that estimate on the polling timer. On narrow screens, model guidance and output
parameters are folded into accordions to keep the submission view shorter.

Failed runs clean up output files created by that failed request when possible.
Queue-backed failures keep the persisted input path in the task row so the failed
task can still be inspected by request id.

Automatic cleanup is disabled by default. To prune old successful history items, set
`PIXLOOM_HISTORY_RETENTION_DAYS` to a positive number. Cleanup runs when the app
starts and when the task list is refreshed.

## Runtime Limits

The service defaults to:

- max input side: `2048px`
- max output side: `8192px`
- tile size: `256`
- tile overlap: `16`
- history items shown: `60`
- history retention: `0 days` means disabled
- SQLite DB path: `state/pixloom.sqlite3`

Override these with environment variables in `compose.yml`:

```yaml
environment:
  PIXLOOM_DB_PATH: "state/pixloom.sqlite3"
  PIXLOOM_MAX_INPUT_SIDE: "2048"
  PIXLOOM_MAX_OUTPUT_SIDE: "8192"
  PIXLOOM_TILE_SIZE: "256"
  PIXLOOM_TILE_OVERLAP: "16"
  PIXLOOM_HISTORY_LIMIT: "60"
  PIXLOOM_HISTORY_RETENTION_DAYS: "0"
```

## Optional Gradio Auth

Pixloom can enable Gradio's built-in basic auth:

```yaml
environment:
  GRADIO_AUTH_USER: "your-user"
  GRADIO_AUTH_PASS: "your-password"
```

This is only a fallback for local or LAN-only use. Public access should still be protected at nginx or a unified authentication layer.

## nginx Reverse Proxy Example

Host nginx should own HTTPS, public hostname, upload size limits, proxy timeout, and login.

```nginx
server {
    listen 443 ssl http2;
    server_name upscale.example.com;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 1800s;
        proxy_send_timeout 1800s;
    }
}
```

Add Basic Auth, Authelia, OAuth2 Proxy, or the existing NAS login layer in nginx.

## Tests

```bash
docker run --rm -v "$PWD:/workspace" -w /workspace pixloom-upscale-webui python -m pytest -q
```

The test suite uses fake models and generated tiny images. It does not require real
model downloads.

## Manual Acceptance Test

Record one real NAS test after placing at least one model in `models/`:

```text
Date: 2026-04-30
Device: Debian 13 x86_64, Docker CPU-only
Input file: input/image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0.png
Input size: 1402x1122
Model: Real-ESRGAN 4x Anime
Output format: PNG
Elapsed time: 92.11s
Output size: 5608x4488
Output path: output/20260430-031033-809102_image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0_realesrgan-x4plus-anime_4x.png
Result notes: CPU-only upscale completed successfully and the output file was written under output/
```

Acceptance criteria:

- phone browser opens the WebUI
- one image uploads successfully
- at least one installed model appears
- CPU upscaling completes
- preview renders
- download file is available
- output file exists under `output/`
- container restart does not remove model or output files
