# Pixloom

**NAS 上的 CPU 图片放大工具 — 单容器、浏览器操作、开箱即用。**

[![Docker Pulls](https://img.shields.io/docker/pulls/alexisks/pixloom)](https://hub.docker.com/r/alexisks/pixloom)

---

## 运行

```bash
docker run -d \
  --name pixloom \
  --restart unless-stopped \
  -p 7860:7860 \
  -v /srv/pixloom:/data \
  alexisks/pixloom:latest
```

打开 `http://<你的NAS_IP>:7860`。

## Compose

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

## 镜像说明

- **纯 CPU 推理**，不需要 GPU / CUDA
- 单端口 `7860`，FastAPI 同时提供 API 和前端
- 内置 16 个预配置超分模型，首次启动自动补齐到 `/data/models`
- SQLite 任务队列，不依赖外部数据库或 Redis
- 输出格式：PNG / JPG / WEBP（JPG 和 WEBP 质量固定 100）

## 数据目录

挂载一个 `/data` 目录，其余路径由容器内部分配：

| 路径 | 内容 |
|------|------|
| `/data/models` | 模型文件 |
| `/data/input` | 上传原图 |
| `/data/output` | 放大结果 |
| `/data/logs` | 请求日志 |
| `/data/state/pixloom.sqlite3` | 任务数据库 |

## 健康检查

```bash
curl http://127.0.0.1:7860/api/health
# → {"status":"ok","runtime":"cpu-only","models_installed":17,"models_operator":16}
```

## 环境变量

可选，默认值已适配 NAS 场景：

- `PIXLOOM_MAX_INPUT_SIDE` — 输入图片最大边长
- `PIXLOOM_MAX_OUTPUT_SIDE` — 输出图片最大边长
- `PIXLOOM_MAX_UPLOAD_BYTES` — 上传大小上限
- `PIXLOOM_TILE_SIZE` — 推理分块大小
- `PIXLOOM_TILE_OVERLAP` — 分块重叠量
- `PIXLOOM_HISTORY_LIMIT` — 任务历史条数
- `PIXLOOM_HISTORY_RETENTION_DAYS` — 历史保留天数

## HTTPS / 认证

镜像本身不处理 HTTPS 和登录。在 NAS 的 nginx / Caddy 前面套一层反代即可：

```nginx
location / {
    proxy_pass http://127.0.0.1:7860;
    proxy_read_timeout 600s;
    auth_basic "Pixloom";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

## 更多信息

- 项目主页：[github.com/alexisks/pixloom](https://github.com/alexisks/pixloom)
- 完整模型说明：[MODEL_CATALOG.md](docs/MODEL_CATALOG.md)
- 架构文档：[ARCHITECTURE.md](docs/ARCHITECTURE.md)
