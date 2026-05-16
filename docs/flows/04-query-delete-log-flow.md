# Query, Delete, Log And File Flow

## 1. 模型列表查询

前端通过 `useModels()` 调：

```text
GET /api/models
```

返回内容来自：

- `list_available_models(config.models_dir)`
- `list_installed_models(config.models_dir)`

其中：

- `models` 只返回 `operator` 可见模型
- `hidden_count` 是本地已安装但不在当前下拉里的模型数量

前端当前行为：

- 页面加载后自动选中第一项可用模型
- `ModelPicker` 用 `group_label_zh` 做分组
- `ModelGuidance` 展示单模型说明

## 2. 任务列表查询

前端通过 `useTasks(60)` 调：

```text
GET /api/tasks?limit=60
```

刷新策略：

- `refetchInterval = 3000ms`
- `staleTime = 2000ms`

也就是说，任务区本质上是一个轻轮询面板。

## 3. `/api/tasks` 返回什么

`backend/pixloom_api/routers/tasks.py` 会把 SQLite 任务行转成前端结构，包含：

- 状态标签
- 输入/输出路径
- 进度值
- 进度说明
- 输出尺寸标签
- 错误码
- 错误详情

同时还返回汇总：

- `queued`
- `running`
- `completed`
- `failed`
- `deleted`
- `interrupted`

## 4. 自动清理信息

`GET /api/tasks` 会顺手调用：

```text
cleanup_expired_history(config)
```

如果 `PIXLOOM_HISTORY_RETENTION_DAYS > 0`：

- 会删除过期历史文件
- summary 里会附带本次清理说明

如果是 `0`：

- 自动清理关闭

## 5. 结果文件访问

前端图片预览和下载并不直接用磁盘路径，而是走：

```text
/api/files/output/{filename}
```

输入文件也有对应访问接口：

```text
/api/files/input/{filename}
```

`files.py` 会做路径边界检查，防止越出根目录。

## 6. 请求日志查看

前端选中某个任务后，通过：

```text
GET /api/logs/{request_id}
```

后端并不返回整份 JSONL 文件，而是：

- 扫描 `logs/pixloom-*.jsonl`
- 只取与该 `request_id` 有关的行
- 生成简短 excerpt

这就是任务详情里日志片段的真实来源。

## 7. 删除任务

前端删除动作：

```text
DELETE /api/tasks/{request_id}
```

后端真实删除链路：

1. 重新从 SQLite 查任务
2. 拒绝删除 `running` 任务
3. 安全解析输入/输出文件路径
4. 只删落在运行目录内的文件
5. 把任务标记成 `deleted`
6. 记录 `task_deleted`

这里的关键点是：

- 删除不是单纯删数据库行
- 会同时删磁盘上的输入/输出文件
- 但只删被证明在运行目录内的安全路径

## 8. 当前 UI 信息流

页面右侧 `TaskPanel` 负责以下信息流：

- 选中任务的结果预览固定显示在任务列表上方
- 任务过滤
- 全选当前过滤列表里的已完成任务
- 批量下载已完成结果
- 结果预览
- 任务行缓存缩略图
- 任务详情展开
- 日志摘录显示
- 同一批次同时存在成功和失败/中断任务时显示部分完成提示

它读的是后端任务契约，不自己拼接业务状态。

## 9. 当前功能边界

从真实代码看，当前系统明确支持：

- 单机 CPU 推理
- 单容器运行
- 多图上传
- 一个批次对应多任务
- 串行后台处理
- 结果预览与下载
- 任务删除
- 请求级 JSONL 审计

当前系统明确不支持：

- GPU 推理
- 多 worker 并行推理
- 用户鉴权
- 多租户
- 模型在线下载市场
- 自动重试策略

## 10. 真相边界总结

如果只记住一件事，应该记住这条：

### 当前 Pixloom 的真相边界

- 配置真相：`app/config.py`
- 模型真相：`app/model_registry.py`
- 任务状态真相：`app/tasks.py` / SQLite
- 推理真相：`app/inference.py`
- 日志真相：`app/request_logging.py` / JSONL
- UI 真相：`frontend/src/app/page.tsx` + hooks + `/api/*`

所以任何功能流程问题，最终都应该回到这些文件看“现在代码实际做了什么”，而不是看历史计划或旧 README。
