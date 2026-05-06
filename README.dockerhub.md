# Pixloom

Pixloom 是一个面向 NAS 的单容器、CPU-only 图片放大控制台。

这个镜像里包含：

- FastAPI 后端
- 静态导出的 React/Next.js 前端
- SQLite 任务队列
- 首次启动可自动落盘的内置模型包
- 中文优先操作界面

这个镜像里不包含：

- GPU 支持
- ComfyUI 式工作流图
- 自动模型下载
- 对外认证层

## CPU-only

本镜像明确是 `CPU-only`：

- PyTorch CPU 版本
- ONNX 只走 CPU provider
- 没有 CUDA / ROCm / Vulkan

## 首次启动

镜像内置模型目录：

```text
/app/bundled-models
```

容器启动时，会把运行目录里缺失的模型文件自动复制到：

```text
/data/models
```

已存在的运行时模型不会被覆盖。

## 目录挂载

建议宿主机准备一个统一数据根目录，例如：

```text
/srv/pixloom/
├── models/
├── input/
├── output/
├── logs/
└── state/
```

容器内固定路径：

- `/data/models`
- `/data/input`
- `/data/output`
- `/data/logs`
- `/data/state/pixloom.sqlite3`

也就是说，宿主机默认只需要把一个目录挂到 `/data`，容器内部再自行分成 `models / input / output / logs / state`。

## docker run

```bash
docker run -d \
  --name pixloom \
  --restart unless-stopped \
  -p 7860:7860 \
  -e PIXLOOM_BUNDLED_MODELS_DIR=/app/bundled-models \
  -e PIXLOOM_MODELS_DIR=/data/models \
  -e PIXLOOM_INPUT_DIR=/data/input \
  -e PIXLOOM_OUTPUT_DIR=/data/output \
  -e PIXLOOM_LOGS_DIR=/data/logs \
  -e PIXLOOM_DB_PATH=/data/state/pixloom.sqlite3 \
  -e PIXLOOM_MAX_INPUT_SIDE=2048 \
  -e PIXLOOM_MAX_OUTPUT_SIDE=8192 \
  -e PIXLOOM_MAX_UPLOAD_BYTES=26214400 \
  -e PIXLOOM_TILE_SIZE=256 \
  -e PIXLOOM_TILE_OVERLAP=16 \
  -e PIXLOOM_HISTORY_LIMIT=60 \
  -e PIXLOOM_HISTORY_RETENTION_DAYS=0 \
  -v /srv/pixloom:/data \
  alexisks/pixloom:latest
```

打开：

```text
http://<宿主机IP>:7860
```

## Docker Compose

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
      PIXLOOM_MAX_INPUT_SIDE: 2048
      PIXLOOM_MAX_OUTPUT_SIDE: 8192
      PIXLOOM_MAX_UPLOAD_BYTES: 26214400
      PIXLOOM_TILE_SIZE: 256
      PIXLOOM_TILE_OVERLAP: 16
      PIXLOOM_HISTORY_LIMIT: 60
      PIXLOOM_HISTORY_RETENTION_DAYS: 0
    volumes:
      - /srv/pixloom:/data
```

启动：

```bash
docker compose up -d
```

## 健康检查

```bash
curl http://127.0.0.1:7860/api/health
```

示例：

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 14,
  "models_operator": 12
}
```

## 说明

- 当前 `8K` 只是最终最长边目标，不是多段链式放大
- 镜像体积较大，因为内置了模型包
- 如果你自己挂载了 `/data/models`，运行时目录始终优先生效
