# Pixloom

Pixloom 是一个面向 NAS 场景的单容器、CPU-only 图片放大控制台。

它的目标很明确：

- 用浏览器上传一张或一小批图片
- 选择一个本地模型
- 放进后台串行队列慢慢跑
- 回来看结果、下载结果、查看日志

它不是 ComfyUI，不是工作流编排器，也不是 GPU 图像实验室。

## 项目定位

当前版本的产品边界非常收敛：

- 单容器部署
- 单端口对外：`7860`
- 单机 CPU 推理
- SQLite 任务队列
- 中文优先操作界面
- 首次启动自动补齐内置模型

## CPU-only 说明

Pixloom 当前明确是 `CPU-only` 项目。

- 镜像内安装的是 PyTorch CPU 轮子
- ONNX 只走 `CPUExecutionProvider`
- 人脸修复模型也只在 CPU 上运行
- `/api/health` 会返回 `"runtime": "cpu-only"`

当前没有以下能力：

- CUDA
- ROCm
- Vulkan / ncnn
- 混合 CPU/GPU 推理

## 直接使用已上传镜像

当前已上传的镜像仓库：

```text
alexisks/pixloom:latest
```

如果只是部署，不需要本地 build，直接拉这个镜像即可。

## 目录挂载约定

建议在宿主机准备一个统一数据根目录，例如：

```text
/srv/pixloom/
├── models/
├── input/
├── output/
├── logs/
└── state/
```

这几个目录的含义：

- `models/`：运行时模型目录
- `input/`：上传原图
- `output/`：放大结果
- `logs/`：JSONL 请求日志
- `state/`：SQLite 任务库

容器内固定使用：

```text
/data/models
/data/input
/data/output
/data/logs
/data/state/pixloom.sqlite3
```

也就是说，**宿主机只需要挂载一个 `/srv/pixloom` 到容器里的 `/data`**。
内部依然会按 `models / input / output / logs / state` 分目录管理，但部署时不需要写五条挂载。

## Docker Compose 部署

推荐部署方式：

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

查看状态：

```bash
docker compose ps
docker compose logs -f --tail=120 pixloom
```

## docker run 部署

如果你不想写 `compose.yml`，可以直接这样启动：

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

停止和删除：

```bash
docker stop pixloom
docker rm pixloom
```

## 首次启动的模型行为

镜像里自带一套内置模型，位置是：

```text
/app/bundled-models
```

启动时，Pixloom 会把“运行目录里缺失的模型文件”自动复制到：

```text
/data/models
```

规则是：

- 首次空目录启动时，会自动补齐模型
- 已存在的运行时模型文件不会被覆盖
- 你后续手动替换 `/data/models` 里的模型，始终以你自己的文件为准

也就是说，空白数据目录也能“开箱即用”。

## 模型选择逻辑

界面里的模型按用途分组，不按论文名字分组。

当前分组：

- `照片主力`
- `照片高质量慢跑`
- `动漫/线稿`
- `人脸修复`
- `快速试跑`
- `经典旧将`

每个模型后面会显示星级，表示它在当前组里的推荐优先级：

- `★★★★★`：当前组第一推荐
- `★★★★☆`：强力备选
- `★★★☆☆`：通用/兜底/试跑
- `★★☆☆☆`：慢速专项
- `★☆☆☆☆`：实验用途

## 当前默认可见模型

### 照片主力

- `SPAN 4x` `★★★★★`
- `RealPLKSR 4x` `★★★★★`
- `照片修复 - 4x NMKD-Siax` `★★★★☆`
- `锐化插画 - 4x UltraSharp` `★★★★☆`

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

## 输出尺寸规则

当前可选：

```text
native
2k
4k
8k
```

含义：

- `native`：按模型原始倍率输出
- `2k`：最终最长边 `2048px`
- `4k`：最终最长边 `4096px`
- `8k`：最终最长边 `8192px`

注意：

- 只保留长宽比，不裁切
- `8K` 只是最终目标尺寸，不代表凭空增加真实细节
- 当前默认不做 `2K -> 4K -> 8K` 链式多段放大

## 健康检查

```bash
curl http://127.0.0.1:7860/api/health
```

示例返回：

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 14,
  "models_operator": 12
}
```

## 常用运维命令

查看容器日志：

```bash
docker logs -f --tail=120 pixloom
```

查看任务接口：

```bash
curl http://127.0.0.1:7860/api/tasks
```

查看模型接口：

```bash
curl http://127.0.0.1:7860/api/models
```

## 相关文档

- 架构说明：[docs/ARCHITECTURE.md](/home/projects/pixloom/docs/ARCHITECTURE.md)
- 完整模型清单：[docs/MODEL_CATALOG.md](/home/projects/pixloom/docs/MODEL_CATALOG.md)
