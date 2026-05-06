# Pixloom

Pixloom is a self-hosted, single-container, CPU-only image upscaling console for
NAS use. It is built for "upload, queue, leave it running, come back later", not
for interactive GPU tinkering.

The product contract is intentionally narrow:

- one Docker Compose service
- one external port: `7860`
- one CPU-only inference stack
- one SQLite task queue
- one Chinese-first operator UI
- one bundled first-boot model pack

Pixloom is not ComfyUI, not a workflow graph, not a model downloader, and not a
GPU image lab.

## What It Does

- upload one image or a small batch
- choose a locally installed model
- see grouped model guidance before submit
- run sequential CPU upscaling in the background
- preview results and download outputs
- keep tasks, inputs, outputs, and logs on disk

## CPU-Only Contract

Pixloom is CPU-only by design.

- PyTorch is installed from the CPU wheel index in the image
- ONNX models run through `CPUExecutionProvider`
- face restoration is forced to CPU
- `/api/health` reports `"runtime": "cpu-only"`

There is no CUDA, ROCm, Vulkan, ncnn, or mixed CPU/GPU mode in the current
release.

## Runtime Shape

```text
browser
  -> http://NAS:7860
     -> FastAPI
        -> static React/Next.js export
        -> /api/*
        -> in-process worker
        -> SQLite queue
        -> CPU-only inference
        -> /data models/input/output/logs/state
```

## Quick Start

```bash
docker compose up -d --build
```

Open:

```text
http://<your-nas-ip>:7860
```

## Data And Storage

Runtime storage lives in the repo root and is mounted into `/data` in the
container:

- `models/` -> `/data/models`
- `input/` -> `/data/input`
- `output/` -> `/data/output`
- `logs/` -> `/data/logs`
- `state/` -> `/data/state`

SQLite task state lives in:

```text
state/pixloom.sqlite3
```

Task statuses:

```text
queued
running
completed
failed
deleted
interrupted
```

## Bundled Models

The image contains a bundled model pack under:

```text
/app/bundled-models
```

On startup, Pixloom copies any missing bundled files into the runtime
`/data/models` directory.

Rules:

- bundled files seed first boot
- runtime files remain the source of truth after boot
- existing runtime files are never overwritten
- manual replacements in `models/` keep winning

This means a fresh empty `/data` mount still starts with a usable model set.

## Model Selection

The dropdown is grouped by use case, not by architecture jargon.

Current groups:

- `照片主力`
- `照片高质量慢跑`
- `动漫/线稿`
- `人脸修复`
- `快速试跑`
- `经典旧将`

Stars show recommended priority inside the current group:

- `★★★★★` first pick
- `★★★★☆` strong fallback
- `★★★☆☆` utility / baseline / smoke test
- `★★☆☆☆` slow specialist
- `★☆☆☆☆` experiment only

The UI does not hide the fact that some models are old. Old but still useful
weights stay visible under `经典旧将` instead of being mixed into the mainline
recommendations.

## Current Operator Set

### 照片主力

- `SPAN 4x` `★★★★★`
- `RealPLKSR 4x` `★★★★★`
- `照片修复 - 4x NMKD-Siax` `★★★★☆`

### 照片高质量慢跑

- `质量上限 - HAT-L 4x` `★★☆☆☆`

### 动漫/线稿

- `APISR 4x` `★★★★★`
- `动漫修复 - Real-CUGAN 3x 去噪` `★★★★★`
- `动漫插画 - Real-ESRGAN Anime 6B` `★★★★☆`

### 人脸修复

- `CodeFormer` `★★★★★`
- `GFPGAN v1.4` `★★★★☆`

### 快速试跑

- `快速试跑 - Real-ESRGAN General v3` `★★★☆☆`

### 经典旧将

- `照片自然 - 4x Remacri` `★★★★☆`
- `照片通用 - Real-ESRGAN 4x` `★★★☆☆`
- `锐化插画 - 4x UltraSharp` `★★★★☆`

## Installed Evaluation Pool

These models can be installed and bundled but are currently hidden from the main
operator dropdown:

- `DAT 4x` `★☆☆☆☆`
- `OmniSR 4x DF2K` `★☆☆☆☆`
- `OmniSR X4 DIV2K` `★☆☆☆☆`

## Output Size Rules

Available presets:

```text
native
2k
4k
8k
```

Meaning:

- `native`: model's own scale
- `2k`: final longest side `2048px`
- `4k`: final longest side `4096px`
- `8k`: final longest side `8192px`

Important:

- Pixloom preserves aspect ratio
- Pixloom does not crop to a fixed canvas
- Pixloom does not promise new real detail just because the target is bigger
- Pixloom does not use chained `2K -> 4K -> 8K` multi-pass upscaling by default

## API

- `GET /api/health`
- `GET /api/models`
- `POST /api/upload`
- `POST /api/batches`
- `GET /api/tasks`
- `DELETE /api/tasks/{request_id}`
- `GET /api/logs/{request_id}`
- `GET /api/files/input/{path}`
- `GET /api/files/output/{path}`

Example health response:

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 16,
  "models_operator": 13
}
```

## Verification

```bash
.venv/bin/pytest -q
cd frontend && npm run lint
cd frontend && npm run build
docker compose build
docker compose up -d
curl http://127.0.0.1:7860/api/health
```

## Logs

Tail container logs:

```bash
docker compose logs -f --tail=120 pixloom
```

Request-level audit logs are stored as JSONL under `logs/`.

## Related Docs

- Architecture: [docs/ARCHITECTURE.md](/home/projects/pixloom/docs/ARCHITECTURE.md)
- Full model catalog: [docs/MODEL_CATALOG.md](/home/projects/pixloom/docs/MODEL_CATALOG.md)
