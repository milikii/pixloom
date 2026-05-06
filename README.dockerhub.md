# Pixloom

Pixloom 是一个面向 NAS 的单容器、CPU-only 图片放大控制台。

它提供：
- FastAPI 后端
- 静态导出的前端界面
- SQLite 任务队列
- 首次启动自动补齐的内置模型包
- 中文优先操作流

它不提供：
- GPU 支持
- ComfyUI 式工作流
- 自动下载外部模型

## 最快启动

宿主机准备一个目录：

```text
/srv/pixloom
```

启动：

```bash
docker run -d \
  --name pixloom \
  --restart unless-stopped \
  -p 7860:7860 \
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
    volumes:
      - /srv/pixloom:/data
```

## 为什么只挂一个目录

容器内部仍然会使用这些路径：
- `/data/models`
- `/data/input`
- `/data/output`
- `/data/logs`
- `/data/state/pixloom.sqlite3`

但部署层默认只需要挂载一个 `/data` 根目录，不需要写五条卷映射。

## 首次启动

镜像内置模型目录：

```text
/app/bundled-models
```

应用启动时会把缺失文件自动补到：

```text
/data/models
```

已存在的运行时模型不会被覆盖。

## 当前镜像状态

- `CPU-only`
- 单端口：`7860`
- 当前内置模型集：`17`
- 当前默认可见模型：`16`
- 隐藏评估模型：`1`（`DAT2 4x 预训练版`）

## 健康检查

```bash
curl http://127.0.0.1:7860/api/health
```

示例：

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 17,
  "models_operator": 16
}
```

## 可选环境变量

默认部署不需要额外环境变量。
只有在你要调整限制时，才需要覆盖这些值：

- `PIXLOOM_MAX_INPUT_SIDE`
- `PIXLOOM_MAX_OUTPUT_SIDE`
- `PIXLOOM_MAX_UPLOAD_BYTES`
- `PIXLOOM_TILE_SIZE`
- `PIXLOOM_TILE_OVERLAP`
- `PIXLOOM_HISTORY_LIMIT`
- `PIXLOOM_HISTORY_RETENTION_DAYS`
