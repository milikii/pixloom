# Worker And Task Lifecycle

## 1. 任务入队后的真实状态

`/api/batches` 成功后，任务先进入 SQLite。

状态流的真实起点是：

- `queued`

不是前端内存状态，也不是日志文本。

## 2. SQLite 中的两张表

`app/tasks.py` 当前维护：

### `batches`

字段重点：

- `id`
- `created_at`
- `model_id`
- `output_format`
- `quality`
- `output_size_preset`
- `total_count`

### `tasks`

字段重点：

- `request_id`
- `batch_id`
- `status`
- `input_filename`
- `input_path`
- `output_path`
- `model_id`
- `output_format`
- `quality`
- `output_size_preset`
- `created_at`
- `started_at`
- `completed_at`
- `elapsed_seconds`
- `progress_value`
- `progress_step`
- `error_code`
- `error_detail`

## 3. worker 如何 claim 任务

`BackgroundTaskWorker` 在循环里调用：

```text
claim_next_queued_task(config)
```

claim 逻辑在 `app/tasks.py` 的 `_claim_queued_task()`：

- `BEGIN IMMEDIATE`
- 取最早的 `queued` 任务
- 改为 `running`
- 写入 `started_at`
- 初始进度写成 `0.02 / 任务已开始`

所以不会出现两个 worker 同时拿到同一条任务的情况。

## 4. worker 如何解析模型

拿到任务后，worker 首先：

1. 调用 `resolve_model()`
2. 用 `task.model_id` 去默认注册表里找模型
3. 检查它是否：
   - `enabled`
   - `operator` 可见
   - 文件确实存在

如果模型不满足条件：

- 任务直接失败
- `error_code = MODEL_NOT_FOUND`

## 5. 推理执行链

worker 真正执行推理时会调用：

```text
run_upscale(...)
```

`run_upscale()` 的真实链路是：

1. `config.ensure_directories()`
2. `validate_upload()`
3. `normalize_output_format()`
4. `build_output_size_plan()`
5. 必要时生成中间预缩放输入
6. `build_output_path()`
7. `BackendRunner.upscale()`
8. 必要时做最终尺寸调整
9. `_save_image()`
10. 写成功日志并返回 `UpscaleResult`

## 6. 后端选择逻辑

`BackendRunner` 当前支持三条后端路径：

- `spandrel`
- `onnxruntime`
- `custom`

对应模型族：

- `spandrel`
  - ESRGAN / RealESRGAN / SPAN / RealPLKSR / HAT / DRCT / Real-CUGAN 等
- `onnxruntime`
  - APISR
- `custom`
  - CodeFormer / GFPGAN

## 7. 输出质量的真实行为

现在的保存行为已经固定：

- `PNG`：不使用质量参数
- `JPEG / WEBP`：质量统一写成 `100`

这是 `app/output_quality.py` 的硬规则，不再受前端控制。

## 8. 进度回写

worker 会通过 `update_task_progress()` 把进度写回 SQLite。

典型步骤包括：

- `正在准备模型`
- `正在推理`
- 后端分块步骤
- `正在写入输出文件`
- `处理完成`

前端 `TaskPanel` 每 3 秒刷新 `/api/tasks`，所以看到的是从 SQLite 回读的真实进度，不是前端猜测。

## 9. 成功路径

成功时：

1. `mark_task_completed()`
2. 状态改成 `completed`
3. 写入 `output_path`
4. 写入 `elapsed_seconds`
5. 写入 `completed_at`
6. 记录 `task_completed` / `request_succeeded` 日志

最终用户可通过：

- `/api/tasks`
- `/api/files/output/{name}`

看到结果和下载文件。

## 10. 失败路径

失败分两层：

### 业务失败

例如：

- 格式不支持
- 图片损坏
- 输出尺寸超限
- 模型文件不存在
- 输出保存失败

这些失败会被封装成 `InferenceError`，携带：

- `code`
- `user_message_zh`
- `likely_cause_zh`
- `suggested_action_zh`
- `detail`
- `request_id`

### worker 崩溃类失败

如果 worker 在 `_process_task()` 外层崩掉：

- 会落成 `WORKER_CRASH`

## 11. 中断与重启

如果服务处理中断：

- 下次启动时所有 `running` 任务会被标成 `interrupted`

所以状态流完整集合是：

- `queued`
- `running`
- `completed`
- `failed`
- `deleted`
- `interrupted`
