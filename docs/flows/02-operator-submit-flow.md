# Operator Submit Flow

## 1. 页面初始化

前端入口在 `frontend/src/app/page.tsx`。

页面初始时会同时读取：

- `useModels()` -> `/api/models`
- `useTasks(60)` -> `/api/tasks?limit=60`

任务日志按选中任务惰性读取：

- `useRequestLog(selectedTaskId)` -> `/api/logs/{request_id}`

## 2. 默认模型选择

页面不会要求用户手动先选模型。

当前真实行为：

- 模型列表加载完成后
- 如果当前没有选中模型
- 或当前选中的模型已不在列表里
- 页面会自动选中第一个可用模型

这一步由 `page.tsx` 里的 `useEffect()` 完成。

## 3. 上传控件

上传区组件是 `frontend/src/components/submission/UploadZone.tsx`。

支持两种入口：

- 点击选择文件
- 拖拽文件到上传区

前端只允许选择这些扩展名：

- `.png`
- `.jpg`
- `.jpeg`
- `.webp`

上传区只负责本地文件选择，不直接进入推理。

## 4. 输出参数选择

当前前端允许用户控制两类输出参数：

1. 输出尺寸 preset
   - `native`
   - `2k`
   - `4k`
   - `8k`
2. 输出格式
   - `PNG`
   - `JPG`
   - `WEBP`

质量参数当前不再暴露给用户。

当前真实行为：

- `JPG / WEBP` 质量固定 `100`
- 前端不再传可变 `quality`
- 后端统一归一到 `100`

## 5. 提交按钮何时可用

提交按钮组件是 `SubmitButton.tsx`。

它会在以下条件下禁用：

- 没有选中文件
- 没有选中模型
- 正在上传或正在创建批次

由于页面会自动选中第一个可用模型，所以常见的灰按钮原因只剩：

- 用户还没选文件
- 或上传/创建正在进行

## 6. 提交流程

点击提交后，`page.tsx` 的 `handleSubmit()` 按两步执行：

1. `useFileUpload().mutateAsync(selectedFiles)`
2. `useSubmitBatch().mutateAsync({...})`

也就是说：

- 先上传文件到服务端输入目录
- 上传成功后再创建批次和任务

## 7. `/api/upload` 真实行为

路由在 `backend/pixloom_api/routers/upload.py`。

每个文件会经历：

1. 写到 `/tmp/<filename>`
2. `validate_upload(tmp, config)`
3. `persist_upload(tmp, config, original_name)`
4. 删除临时 `/tmp` 文件

返回值是：

- `original_name`
- `stored_path`
- `size_bytes`

所以前端真正传给 `/api/batches` 的不是浏览器文件对象，而是后端已经落盘的 `stored_path` 列表。

## 8. `/api/batches` 真实行为

路由在 `backend/pixloom_api/routers/batches.py`。

它会先做三类检查：

1. 是否有 `stored_paths`
2. `output_size_preset` 是否有效
3. `model_id` 是否在 `/api/models` 可见列表里，且模型文件存在

通过后：

1. 生成一个 `batch_id`
2. 为每张图生成一个 `request_id`
3. 组装 `QueuedTaskInput`
4. 调用 `create_batch_with_tasks()`

当前质量规则：

- 请求体里 `quality` 可以为空
- 即使传了别的值，也会被 `normalize_output_quality()` 归一成 `100`

## 9. 批次创建成功后前端动作

批次创建成功后，前端会：

- 记住 `first_request_id`
- 清空当前选中的浏览器文件
- 让任务面板自动切到首个任务

`useSubmitBatch()` 成功后还会自动刷新任务查询缓存。

## 10. 失败路径

前端提交失败时，`handleSubmit()` 会把错误消息落到 `submitError`。

错误来源可能是：

- 上传验证失败
- 模型不可用
- 批次创建失败
- 网络请求失败

这块展示的是面向操作者的中文错误信息，不是原始 traceback。
