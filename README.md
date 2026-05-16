# Pixloom

在 NAS 上运行的 CPU 图片放大工具。浏览器上传 → 选模型 → 队列处理 → 下载结果。

**单容器、单端口、零依赖部署。**

---

## 为什么选 Pixloom

大多数图片放大工具要么需要 GPU，要么是 ComfyUI 那样重的工作流引擎。Pixloom 只解决一个问题：在你的 NAS 上，用浏览器完成 CPU 图片放大。

- 单容器，挂一个 `/data` 目录即可运行
- 纯 CPU 推理，不依赖 CUDA 或独立显卡
- SQLite 管理任务队列，不需要 Redis 或外部数据库
- 内置 16 个预配置模型，首次启动自动就绪
- 中文界面优先，手机浏览器可用

**Pixloom 不做的事：** GPU 加速、ComfyUI 式工作流、在线模型下载、用户账户系统。如果你需要这些，考虑 ComfyUI 或 chaiNNer。

---

## 快速开始

```bash
docker run -d \
  --name pixloom \
  --restart unless-stopped \
  -p 7860:7860 \
  -v /srv/pixloom:/data \
  alexisks/pixloom:latest
```

打开 `http://<NAS_IP>:7860`。

**Docker Compose：**

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

---

## 数据目录

只挂载一个 `/data` 目录，内部自动组织：

```
/data/models/              # 模型文件
/data/input/               # 上传的原图
/data/output/              # 放大后的图片
/data/thumbnails/          # 任务列表缩略图缓存
/data/logs/                # 请求审计日志
/data/state/pixloom.sqlite3 # 任务状态
```

默认会保留最近 30 天的任务文件；临时批量下载 zip 保留 24 小时并在下载完成后尽快删除。前端“存储状态”面板会显示模型、上传原图、放大结果、缩略图、日志、状态数据库和临时下载包的占用。

---

## 内置模型

镜像预装 16 个可见模型 + 1 个隐藏评估模型，分 6 组。首次启动自动从 `/app/bundled-models` 补齐到 `/data/models`，已有文件不覆盖。

| 分组 | 模型 | 星级 |
|------|------|:--:|
| **照片主力** | SPAN 4x · RealPLKSR 4x · NMKD-Siax 4x · UltraSharp 4x | ★★★★ |
| **高质量慢跑** | DRCT 4x · HAT-L 4x · DRCT-L 4x | ★★★ |
| **动漫/线稿** | APISR 4x · Real-CUGAN 3x · Real-CUGAN 2x · Real-ESRGAN Anime 6B | ★★★★ |
| **人脸修复** | CodeFormer · GFPGAN v1.4 | ★★★★ |
| **快速试跑** | Real-ESRGAN General v3 | ★★★ |
| **经典旧将** | 4x Remacri · Real-ESRGAN 4x | ★★★ |

完整模型说明和选型建议见 [模型目录](docs/MODEL_CATALOG.md)。

---

## 输出尺寸

| 预设 | 最长边 |
|------|--------|
| `native` | 模型原始倍率 |
| `2k` | 2048px |
| `4k` | 4096px |
| `8k` | 8192px |

JPG/WEBP 输出质量固定 100，PNG 无损。

---

## API

```bash
# 健康检查
curl http://127.0.0.1:7860/api/health
# → {"status":"ok","runtime":"cpu-only","models_installed":17,"models_operator":16}

# 模型列表
curl http://127.0.0.1:7860/api/models

# 任务列表
curl http://127.0.0.1:7860/api/tasks

# 存储状态
curl http://127.0.0.1:7860/api/storage
```

---

## 可选环境变量

默认不需要设置。仅在需要调整限制时覆盖：

| 变量 | 用途 |
|------|------|
| `PIXLOOM_MAX_INPUT_SIDE` | 输入图片最大边长 |
| `PIXLOOM_MAX_OUTPUT_SIDE` | 输出图片最大边长 |
| `PIXLOOM_MAX_UPLOAD_BYTES` | 上传文件大小上限 |
| `PIXLOOM_TILE_SIZE` | 推理分块大小 |
| `PIXLOOM_TILE_OVERLAP` | 分块重叠像素 |
| `PIXLOOM_HISTORY_LIMIT` | 历史记录条数上限 |
| `PIXLOOM_HISTORY_RETENTION_DAYS` | 任务文件保留天数，默认 30；设为 0 可关闭 |
| `PIXLOOM_ARCHIVE_TTL_HOURS` | 临时批量下载 zip 保留小时数，默认 24 |
| `PIXLOOM_THUMBNAIL_DIR` | 缩略图缓存目录 |

---

## 架构

FastAPI 后端 + React/Next.js 静态前端，同进程串行队列。详见 [架构文档](docs/ARCHITECTURE.md)。

```
浏览器 → :7860 → FastAPI（API + 静态文件 + 后台推理 worker）
                   ├── SQLite 任务队列
                   ├── Spandrel/PyTorch CPU 推理
                   └── 文件系统存储
```

---

## 开发

```bash
# 后端
cd backend && pip install -r requirements.txt
pytest -q

# 前端
cd frontend && npm ci && npm run build

# 构建镜像
docker compose build
```
