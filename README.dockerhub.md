# Pixloom

Pixloom is a single-container, CPU-only image upscaling console for NAS use.

What you get in this image:

- FastAPI backend
- static React/Next.js frontend
- SQLite task queue
- bundled first-boot model pack
- Chinese-first operator UI

What you do **not** get:

- GPU support
- ComfyUI-style graph workflows
- model downloader
- public auth layer

## CPU-Only

This image is CPU-only.

- PyTorch CPU wheels
- ONNX CPU provider only
- no CUDA / ROCm / Vulkan path

## First Boot

The image contains bundled models under `/app/bundled-models`.

On startup, Pixloom copies any missing bundled files into the runtime
`/data/models` directory. Existing runtime files are never overwritten.

## Quick Run

```bash
docker run -d \
  --name pixloom \
  -p 7860:7860 \
  -e PIXLOOM_BUNDLED_MODELS_DIR=/app/bundled-models \
  -e PIXLOOM_MODELS_DIR=/data/models \
  -e PIXLOOM_INPUT_DIR=/data/input \
  -e PIXLOOM_OUTPUT_DIR=/data/output \
  -e PIXLOOM_LOGS_DIR=/data/logs \
  -e PIXLOOM_DB_PATH=/data/state/pixloom.sqlite3 \
  -v /your/path/pixloom-data:/data \
  alexisks/pixloom:latest
```

Open:

```text
http://<host>:7860
```

## Docker Compose Example

```yaml
services:
  pixloom:
    image: alexisks/pixloom:latest
    container_name: pixloom
    restart: unless-stopped
    ports:
      - "7860:7860"
    environment:
      PIXLOOM_BUNDLED_MODELS_DIR: /app/bundled-models
      PIXLOOM_MODELS_DIR: /data/models
      PIXLOOM_INPUT_DIR: /data/input
      PIXLOOM_OUTPUT_DIR: /data/output
      PIXLOOM_LOGS_DIR: /data/logs
      PIXLOOM_DB_PATH: /data/state/pixloom.sqlite3
    volumes:
      - ./data:/data
```

## Storage

Runtime storage layout:

- `/data/models`
- `/data/input`
- `/data/output`
- `/data/logs`
- `/data/state/pixloom.sqlite3`

## Model Groups

The UI groups models by operator intent:

- `照片主力`
- `照片高质量慢跑`
- `动漫/线稿`
- `人脸修复`
- `快速试跑`
- `经典旧将`

Stars indicate priority inside the current group:

- `★★★★★` first pick
- `★★★★☆` strong fallback
- `★★★☆☆` utility / baseline
- `★★☆☆☆` slow specialist
- `★☆☆☆☆` experiment only

## Health

`GET /api/health`

Example:

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 16,
  "models_operator": 13
}
```

## Notes

- 8K is a final longest-side target, not a chained multi-pass upscale mode
- this image is large because it includes bundled models
- if you already have your own preferred weights, mount them into `/data/models`
  and they will override the bundled seed set
