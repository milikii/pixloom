# Pixloom Flows

本目录按“真实代码当前行为”反写 Pixloom 的完整功能流程。

这些文档不是产品设想，也不是旧版本计划稿。它们以当前代码为准，覆盖：

- 启动与运行时初始化
- 前端操作流
- 上传、批次创建、任务入队
- 后台 worker 串行处理
- 任务查询、结果下载、日志查看
- 删除、清理与文件系统真相

推荐阅读顺序：

1. [01-runtime-startup.md](./01-runtime-startup.md)
2. [02-operator-submit-flow.md](./02-operator-submit-flow.md)
3. [03-worker-task-lifecycle.md](./03-worker-task-lifecycle.md)
4. [04-query-delete-log-flow.md](./04-query-delete-log-flow.md)

当前代码入口参考：

- FastAPI 应用入口：`backend/pixloom_api/main.py`
- 后台 worker：`backend/worker/daemon.py`
- 任务与 SQLite：`app/tasks.py`
- 推理与文件落盘：`app/inference.py`
- 前端页面：`frontend/src/app/page.tsx`
