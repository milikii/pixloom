# Runtime Startup Flow

## 1. 进程入口

当前容器启动命令是：

```text
python -m uvicorn backend.pixloom_api.main:app --host 0.0.0.0 --port 7860
```

应用创建在 `backend/pixloom_api/main.py`。

## 2. FastAPI 生命周期

应用启动时，`lifespan()` 按固定顺序执行：

1. `load_config()`
2. `config.ensure_directories()`
3. `sync_bundled_models(config)`
4. `initialize_task_store(config)`
5. `mark_running_tasks_interrupted(config)`
6. 创建并启动 `BackgroundTaskWorker`
7. 把 `config` 和 `worker` 放到 `app.state`

这意味着运行时初始化不是散落在各个路由里，而是有一个统一启动阶段。

## 3. 配置来源

配置定义在 `app/config.py`。

当前运行时核心路径：

- `PIXLOOM_MODELS_DIR` -> `/data/models`
- `PIXLOOM_INPUT_DIR` -> `/data/input`
- `PIXLOOM_OUTPUT_DIR` -> `/data/output`
- `PIXLOOM_LOGS_DIR` -> `/data/logs`
- `PIXLOOM_DB_PATH` -> `/data/state/pixloom.sqlite3`
- `PIXLOOM_BUNDLED_MODELS_DIR` -> `/app/bundled-models`

`ensure_directories()` 会确保：

- `models/`
- `input/`
- `output/`
- `logs/`
- `state/`

这些目录在运行前就存在。

## 4. 内置模型自动落盘

`app/bundled_models.py` 负责把镜像里的 `/app/bundled-models` 同步到运行目录 `/data/models`。

同步规则：

- 只复制缺失文件
- 已存在文件跳过，不覆盖
- 会递归复制子目录，例如 `facelib/`

所以“开箱即用”的真实含义是：

- 镜像内置模型包
- 第一次启动时自动种到运行目录
- 用户以后替换 `/data/models` 内文件时，运行目录优先

## 5. SQLite 初始化

`app/tasks.py` 的 `initialize_task_store()` 负责初始化 `batches` 和 `tasks` 两张表。

当前真实状态源分工：

- SQLite：任务状态、批次元信息、进度、错误
- 文件系统：输入图片、输出图片、模型文件
- JSONL：请求级审计日志

## 6. 中断任务恢复

启动时执行 `mark_running_tasks_interrupted(config)`。

它的作用是：

- 上次进程如果在处理中途退出
- 所有 `running` 任务在启动后会被改成 `interrupted`

所以系统不会把旧的“处理中”状态永远挂在那里。

## 7. 后台 worker 启动

`backend/worker/daemon.py` 会创建一个常驻线程：

- 读取默认模型注册表
- 创建 `BackendRunner`
- 进入轮询循环
- 每 2 秒尝试 claim 一个排队任务

worker 是串行的，一次只处理一个任务。

## 8. 路由挂载

当前公开的 API 路由：

- `/api/health`
- `/api/models`
- `/api/upload`
- `/api/batches`
- `/api/tasks`
- `/api/logs`
- `/api/files`

前端静态导出目录存在时，应用会把 `/` 挂到 `frontend-out`。

## 9. 启动后的稳定状态

启动完成后，系统进入以下稳定结构：

- FastAPI 对外提供 API 和前端静态文件
- SQLite 已可读写
- `/data/models` 已补齐内置模型
- worker 已在后台轮询任务
- 前端可直接读取 `/api/models`、`/api/tasks`
