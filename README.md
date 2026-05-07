# Pixloom

Pixloom 是一个面向 NAS 的单容器、CPU-only 图片放大控制台。

它做的事情很单纯：
- 上传图片
- 选一个本地模型
- 进入后台串行队列
- 回来看结果、下载结果、查任务和日志

它不做这些事：
- 不做 ComfyUI 式工作流
- 不做 GPU 路线
- 不做在线模型市场
- 不做自动拉模型和自动调参

## 为什么是它

Pixloom 的目标不是“功能最多”，而是“在 NAS 上稳定落地”：
- 单容器
- 单端口：`7860`
- 单机 CPU 推理
- SQLite 任务队列
- 中文优先界面
- 首次启动自动补齐内置模型

这意味着它更像一个长期可维护的家用图像处理台，而不是实验室。

## 快速开始

如果你只想部署，直接用已上传镜像：

```text
alexisks/pixloom:latest
```

宿主机只需要准备一个目录，例如：

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

启动：

```bash
docker compose up -d
```

## 数据目录

容器内部固定使用这些路径：

```text
/data/models
/data/input
/data/output
/data/logs
/data/state/pixloom.sqlite3
```

也就是说，部署层只挂一个 `/data` 就够了。
内部仍然按 `models / input / output / logs / state` 分目录管理，但这些不需要用户一条条单独挂载。

## 首次启动会发生什么

镜像自带一套内置模型，位置是：

```text
/app/bundled-models
```

应用启动时会把缺失文件自动补到：

```text
/data/models
```

规则很简单：
- 空目录第一次启动，会自动种出基础模型
- 已存在的运行时模型不会被覆盖
- 你自己替换 `/data/models` 里的文件，运行时目录永远优先生效

## 当前模型矩阵

默认可见模型分 6 组：
- `照片主力`
- `照片高质量慢跑`
- `动漫/线稿`
- `人脸修复`
- `快速试跑`
- `经典旧将`

星级不是论文排名，只是当前组内的推荐优先级：
- `★★★★★` 第一推荐
- `★★★★☆` 强力备选
- `★★★☆☆` 通用或兜底
- `★★☆☆☆` 慢速专项
- `★☆☆☆☆` 实验用途

当前默认可见模型：

### 照片主力

- `SPAN 4x` `★★★★★`
- `RealPLKSR 4x` `★★★★★`
- `照片修复 - 4x NMKD-Siax` `★★★★☆`
- `锐化插画 - 4x UltraSharp` `★★★★☆`

### 照片高质量慢跑

- `DRCT 4x` `★★★★☆`
- `质量上限 - HAT-L 4x` `★★☆☆☆`
- `DRCT-L 4x` `★★☆☆☆`

### 动漫/线稿

- `APISR 4x` `★★★★★`
- `动漫修复 - Real-CUGAN 3x 去噪` `★★★★★`
- `动漫精修 - Real-CUGAN 2x 去噪` `★★★★☆`
- `动漫插画 - Real-ESRGAN Anime 6B` `★★★★☆`

### 人脸修复

- `CodeFormer` `★★★★★`
- `GFPGAN v1.4` `★★★★☆`

### 快速试跑

- `快速试跑 - Real-ESRGAN General v3` `★★★☆☆`

### 经典旧将

- `照片自然 - 4x Remacri` `★★★★☆`
- `照片通用 - Real-ESRGAN 4x` `★★★☆☆`

当前仍保留 1 个隐藏评估模型：
- `DAT2 4x 预训练版`

## 真实图片怎么选

基于当前本机真实样张和已有输出记录，这一版选择建议可以定成下面这样：

### 实拍照片

- `4x Remacri`
  适合人物、旅行照、日常实拍。观感更自然，不会急着把边缘全部推硬。
- `Real-ESRGAN 4x`
  适合当稳定基线。你不确定选什么时，它通常是最稳的起点。
- `4x UltraSharp`
  更适合风景、建筑、AI 图、压缩网图。边缘更利，但人脸和近景细节可能偏硬。
- `4x NMKD-Siax`
  更适合压缩重、噪点多、素材质量不干净的图。
- `SPAN 4x` / `RealPLKSR 4x`
  属于新一代日常主力。画质和速度比旧 ESRGAN 组合更平衡。

### 高质量慢跑

- `DRCT 4x`
  现在是这组里最值得优先试的。砖墙、树叶、布料这类纹理密集场景更有对比价值。
- `HAT-L 4x`
  还是可靠的上限基线，更像“稳重的老旗舰”。
- `DRCT-L 4x`
  只适合极少量样张做上限压榨，不适合日常操作。
- `DAT2 4x 预训练版`
  保留，但不建议放进主流程。因为它是 `pretrain`，不适合拿来代表 DAT 系列最终水平。

### 动漫和线稿

- `APISR 4x`
  适合压缩重、失真明显的动漫图。
- `Real-CUGAN 3x 去噪`
  适合二次元主力放大，线条保护和去噪更稳。
- `Real-CUGAN 2x 去噪`
  适合已经接近 2K 的图，想更克制地精修到 4K。
- `Real-ESRGAN Anime 6B`
  适合轻量兜底，体积小、跑得快。

## 输出尺寸

可选值：

```text
native
2k
4k
8k
```

含义：
- `native`：按模型原始倍率输出
- `2k`：最长边 `2048px`
- `4k`：最长边 `4096px`
- `8k`：最长边 `8192px`

保存格式规则：
- `PNG` 不涉及质量参数
- `JPG / WEBP` 质量固定为 `100`

当前默认不做 `2K -> 4K -> 8K` 链式多段放大。

## 健康检查

```bash
curl http://127.0.0.1:7860/api/health
```

当前镜像的预期返回示例：

```json
{
  "status": "ok",
  "runtime": "cpu-only",
  "models_installed": 17,
  "models_operator": 16
}
```

## 常用命令

查看日志：

```bash
docker logs -f --tail=120 pixloom
```

查看任务：

```bash
curl http://127.0.0.1:7860/api/tasks
```

查看模型：

```bash
curl http://127.0.0.1:7860/api/models
```

## 可选环境变量

如果你只是部署，默认不需要传任何环境变量。
只有在你明确要改限制或行为时，才需要覆盖这些可选项：

- `PIXLOOM_MAX_INPUT_SIDE`
- `PIXLOOM_MAX_OUTPUT_SIDE`
- `PIXLOOM_MAX_UPLOAD_BYTES`
- `PIXLOOM_TILE_SIZE`
- `PIXLOOM_TILE_OVERLAP`
- `PIXLOOM_HISTORY_LIMIT`
- `PIXLOOM_HISTORY_RETENTION_DAYS`

## 相关文档

- 架构说明：[docs/ARCHITECTURE.md](/home/projects/pixloom/docs/ARCHITECTURE.md)
- 完整模型清单：[docs/MODEL_CATALOG.md](/home/projects/pixloom/docs/MODEL_CATALOG.md)
- 模型评估记录：[docs/MODEL_EVALUATION.md](/home/projects/pixloom/docs/MODEL_EVALUATION.md)
