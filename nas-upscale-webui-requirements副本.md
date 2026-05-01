# NAS 自建图片放大 Gradio WebUI 部署需求

## 背景

希望在无 GPU 的 x86 NAS 上部署一个可通过手机浏览器访问的图片放大服务，用来替代外出时无法使用的本地超分软件。

本方案不使用 ComfyUI。目标是自建一个轻量 Gradio WebUI，只保留图片上传、模型选择、图片放大、结果下载这些核心能力。

## 总体目标

- 使用 Docker 或 Docker Compose 部署。
- 使用自建 Python + Gradio WebUI。
- 支持 CPU-only 运行，不依赖 NVIDIA GPU、CUDA 或 ROCm。
- 支持手机浏览器访问。
- 支持上传图片、选择模型、选择放大倍数、执行放大、下载结果。
- 模型、输入图片、输出结果、日志必须持久化。
- 默认不裸奔公网端口，应通过 nginx 反代，并加 HTTPS 和登录鉴权。

## 第一阶段边界

第一阶段目标是“最小可用 NAS 版”，不是一次性做成完整模型平台。

必须先做到：

- 手机浏览器能打开 WebUI。
- 可以上传单张图片。
- 可以选择已安装模型。
- 可以完成 CPU-only 放大。
- 可以预览和下载结果。
- 输出、输入、模型和日志在容器重启后不丢失。

第一阶段不做：

- ComfyUI 式复杂工作流。
- 批量处理。
- 自动模型下载器。
- 用户账号系统。
- 自动 nginx 配置。
- Docker 镜像发布流水线。
- GPU / CUDA / ROCm / ncnn-vulkan 加速。

## 技术路线

推荐实现为：

```text
Gradio WebUI
-> 图片上传
-> 模型选择
-> CPU 推理
-> 保存输出图片
-> 浏览器下载结果
```

后端优先级：

1. `Spandrel + PyTorch CPU`：适合加载 `.pth` / `.safetensors` 模型，支持 ESRGAN、Real-ESRGAN、SwinIR、HAT、DAT、SPAN、PLKSR、RealPLKSR、MoESR、AuraSR 等多种超分架构。
2. `ONNX Runtime CPU`：适合加载 `.onnx` 模型，部署更轻，CPU 兼容性好，适合 NAS 长期运行。
3. `Real-ESRGAN 官方实现`：作为稳定基线方案，适合先跑通 RealESRGAN_x4plus、RealESRGAN_x4plus_anime_6B、realesr-general-x4v3。
4. `ncnn-vulkan`：如果 NAS 支持 Vulkan，可作为后续加速方案；第一阶段不要依赖它。

第一阶段建议优先实现 `Spandrel + PyTorch CPU` 这一条真实推理路径。

同时，模型注册表需要预留以下 backend 字段：

```text
spandrel
onnxruntime
realesrgan
```

但第一阶段不要求同时完成 ONNX Runtime 和 Real-ESRGAN 官方实现。ONNX Runtime 适合作为第二阶段 CPU 性能对比路线；Real-ESRGAN 官方实现只在 Spandrel 无法稳定加载某些基线模型时再补。

这样做的原因：

- 第一阶段先跑通真实 NAS 使用链路，减少依赖和模型格式兼容风险。
- Spandrel 更贴近 `.pth` / `.safetensors` 超分模型生态。
- ONNX 模型需要单独确认输入输出张量约定，第一天容易拖慢交付。
- Real-ESRGAN 官方实现可作为兼容兜底，但不应成为第一阶段的额外复杂度。

## 推荐目录结构

```text
/volume1/docker/upscale-webui/
  compose.yml
  app/
    app.py
    inference.py
    model_registry.py
    requirements.txt
    Dockerfile
  tests/
  models/
    realesrgan/
    esrgan/
    onnx/
  input/
  output/
  logs/
  README.md
```

目录用途：

- `compose.yml`：Docker Compose 配置。
- `app/app.py`：Gradio WebUI 入口。
- `app/inference.py`：图片放大推理逻辑。
- `app/model_registry.py`：模型配置、名称、路径、类型、默认参数。
- `app/requirements.txt`：Python 依赖。
- `app/Dockerfile`：CPU-only 镜像构建文件。
- `tests/`：pytest 测试，使用 fake backend，不依赖真实大模型。
- `models/`：存放放大模型。
- `input/`：保存上传原图。
- `output/`：保存放大结果。
- `logs/`：保存运行日志。
- `README.md`：记录部署、更新、加模型、反代和测试方法。

## WebUI 功能要求

Gradio 页面至少包含：

- 图片上传控件。
- 模型选择下拉框。
- 放大倍数显示，优先支持 4x 模型。
- 可选参数：
  - 输出格式：PNG / JPG / WEBP。
  - JPG/WebP 质量。
  - 是否保留原文件名。
  - 是否自动限制最大输入分辨率。
- 开始处理按钮。
- 输出图片预览。
- 下载按钮。
- 简单状态提示：
  - 当前模型。
  - 输入尺寸。
  - 输出尺寸。
  - 推理耗时。
  - 输出文件路径。

手机端要求：

- 页面宽度适配手机浏览器。
- 控件不要过多，不做复杂工作流编辑器。
- 默认模型应适合大多数图片。
- 处理完成后能直接下载结果。

## 模型推进顺序

注意：以下模型分为“稳定基线”和“较新架构测试”。`RealESRGAN_x4plus`、`RealESRGAN_x4plus_anime_6B`、`4x-UltraSharp`、`4x-Remacri` 不是最新模型，而是生态成熟、资料多、最适合先跑通服务的基线模型。

### 第一阶段：稳定基线模型

先安装这些模型，目标是保证功能跑通、效果稳定、方便对比。

#### RealESRGAN_x4plus

用途：

- 通用照片。
- 真实图片。
- 普通压缩图片。

特点：

- Real-ESRGAN 官方通用模型。
- 适合作为默认照片放大模型。
- 效果稳定，但 CPU 推理会比较慢。
- 不是最新模型，但兼容性和资料最稳。

建议 WebUI 名称：

```text
Real-ESRGAN 4x Photo
```

#### RealESRGAN_x4plus_anime_6B

用途：

- 动漫图。
- 插画。
- 线稿。
- 二次元风格图片。

特点：

- 模型较小。
- CPU 环境相对友好。
- 适合色块、边缘、线稿类图片。
- 不是最新模型，但适合作为动漫/插画基线。

建议 WebUI 名称：

```text
Real-ESRGAN 4x Anime
```

#### realesr-general-x4v3

用途：

- 通用轻量放大。
- CPU 环境下优先测试。
- 速度优先场景。

特点：

- Real-ESRGAN 官方较轻量模型。
- 比 `RealESRGAN_x4plus` 更适合弱 CPU 设备试跑。
- 适合作为低性能 NAS 的备选默认模型。

建议 WebUI 名称：

```text
Real-ESRGAN General 4x v3
```

#### 4x-UltraSharp

用途：

- AI 生成图。
- 插画。
- 一般图片锐化增强。
- 想要更清晰观感的图片。

特点：

- 锐化感明显。
- 结果观感直接。
- 很适合作为常用增强模型。
- 属于成熟常用模型，不是最新架构。

建议 WebUI 名称：

```text
4x UltraSharp
```

#### 4x-Remacri / 4x_foolhardy_Remacri

用途：

- 照片。
- 混合内容图片。
- 希望细节更自然的场景。

特点：

- 细节相对自然。
- 适合作为照片和通用图片的备选模型。
- 属于成熟常用模型，不是最新架构。

建议 WebUI 名称：

```text
4x Remacri
```

### 第二阶段：较新架构测试模型

以下模型更接近“较新模型/较新架构”的方向，但 CPU 速度、依赖兼容性和模型文件来源都需要实测。不建议第一天就作为唯一主力，应在稳定基线跑通后加入。

#### SPAN 系列

用途：

- 通用图片放大。
- 动漫、插画、AI 图增强。
- 需要在效果和速度之间折中的场景。

特点：

- 架构相对较新。
- 通常比大型 Transformer 类模型更适合 CPU 测试。
- 建议通过 Spandrel 加载支持的 `.pth` 或 `.safetensors` 模型。

建议 WebUI 名称：

```text
SPAN 4x
```

#### RealPLKSR / PLKSR 系列

用途：

- 通用照片。
- AI 图。
- 追求较新架构的轻量测试。

特点：

- 架构较新。
- 相比传统 ESRGAN 系列更值得作为下一阶段重点测试。
- 需要确认具体模型是否被 Spandrel 或 ONNX Runtime 支持。

建议 WebUI 名称：

```text
RealPLKSR 4x
```

#### DAT / ATD 系列

用途：

- 高质量超分对比。
- 照片、插画质量测试。

特点：

- 架构较新，质量潜力较好。
- CPU 推理通常更慢。
- 更适合作为小图质量测试，不适合第一阶段默认模型。

建议 WebUI 名称：

```text
DAT 4x
ATD 4x
```

#### HAT / SwinIR / OmniSR 系列

用途：

- 后续质量对比。
- 特定图片类型优化。

特点：

- 属于较新的高质量超分方向或经典 Transformer 方向。
- 效果可能更好，但 CPU 速度通常较慢。
- 不建议作为第一阶段主力。

#### BSRGAN

用途：

- 压缩较重的图片。
- 模糊图片。
- 真实退化图片修复。

特点：

- 偏真实退化修复。
- 有些图片上会比 Real-ESRGAN 更自然。
- 不是最新模型，但仍然值得保留为修复类基线。

## 推荐模型组合

第一批稳定基线建议安装：

```text
RealESRGAN_x4plus
RealESRGAN_x4plus_anime_6B
realesr-general-x4v3
4x-UltraSharp
4x-Remacri
```

稳定基线使用建议：

- 照片：`RealESRGAN_x4plus`
- 动漫/插画：`RealESRGAN_x4plus_anime_6B`
- 弱 CPU 或快速试跑：`realesr-general-x4v3`
- AI 图/想要更锐：`4x-UltraSharp`
- 照片但希望更自然：`4x-Remacri`

第二批较新模型建议测试：

```text
SPAN 4x 模型
RealPLKSR / PLKSR 4x 模型
DAT / ATD 4x 模型
HAT / SwinIR / OmniSR 4x 模型
```

第二批选择原则：

- 优先选 OpenModelDB 上标注清楚架构、scale、输入类型和适用场景的模型。
- 优先选 Spandrel 已支持的架构，减少手写模型代码。
- 如果有 `.onnx` 版本，优先加入 ONNX Runtime 路线做 CPU 性能对比。
- 每新增一个模型，都要记录输入尺寸、输出尺寸、耗时、内存占用和主观效果。
- 第一阶段模型文件由用户手动放入 `models/`，不做自动下载器。

## 实现要求

### Docker Compose

Compose 至少需要：

- 一个 `upscale-webui` 服务。
- 映射 WebUI 端口，例如容器内 `7860`。
- 挂载 `models/`、`input/`、`output/`、`logs/`。
- 设置重启策略，例如 `unless-stopped`。
- 不默认直接暴露公网。

建议端口：

```text
127.0.0.1:7860 -> 7860
```

如需局域网访问，可以改为：

```text
0.0.0.0:7860 -> 7860
```

公网访问应通过 nginx 反代。

反代边界说明：

- 应用不负责申请证书、配置域名或实现登录系统。
- 宿主机 nginx 负责 HTTPS、域名、登录鉴权和公网入口。
- README 只需要提供 nginx 反代示例和注意事项，不需要自动生成 nginx 配置。
- 如果已有统一入口、Authelia、OAuth2 Proxy 或 Basic Auth，直接在 nginx 层接入。

### Gradio 启动参数

Gradio 应监听：

```text
server_name="0.0.0.0"
server_port=7860
```

如启用 Gradio 自带基础认证，可支持环境变量：

```text
GRADIO_AUTH_USER
GRADIO_AUTH_PASS
```

但公网正式访问仍应交给 nginx 或统一鉴权服务。Gradio 自带 auth 只作为局域网直连或临时访问的兜底，不作为正式安全边界。

### 推理逻辑

推理代码应满足：

- 加载模型时缓存，避免每次处理都重新加载。
- 模型注册表应记录 backend、architecture、scale、path、适用图片类型和备注。
- 至少预留 `spandrel`、`onnxruntime`、`realesrgan` 三种 backend 字段。
- 第一阶段真实推理优先实现 `spandrel` backend。
- `onnxruntime` 和 `realesrgan` backend 字段可以先预留，不要求第一阶段完整实现。
- 输出文件名包含时间戳、模型名和放大倍数。
- 自动记录输入尺寸、输出尺寸和耗时。
- 大图处理前给出限制或自动缩放。
- 默认使用 tiled inference，避免整张大图一次性进模型导致 NAS 内存爆掉。
- tile size 和 overlap 应支持通过环境变量或配置项调整。
- 推理失败时在 WebUI 返回清晰错误。
- 不把用户上传图片保存在临时不可控目录。

建议限制：

```text
默认最大输入边长：2048 px
默认最大输出边长：8192 px
```

限制值可以通过环境变量调整。

### 测试要求

第一阶段需要加入 pytest 测试，但测试不依赖真实大模型。

测试应覆盖：

- 模型注册表只返回 enabled 且文件存在的模型。
- 未知 model id 返回清晰错误。
- 缺失模型文件不会导致页面崩溃。
- 支持 PNG / JPG / JPEG / WEBP。
- 伪装成图片扩展名的无效文件会被 Pillow 解码拦截。
- 超过最大输入尺寸的图片会在推理前被拒绝。
- 输出文件名安全，包含时间戳、模型名和放大倍数。
- 后端异常会被转换成 WebUI 可读错误，而不是直接暴露 traceback。
- Gradio handler 能返回预览、下载文件和状态文本。

真实模型测试作为 NAS 上的手动验收测试记录到 README。

## 性能预期

无 GPU 环境下，超分会明显慢于本地 GPU 软件。

建议初期使用方式：

- 单张图片处理。
- 优先处理中小尺寸图片。
- 优先 4x 模型，但限制输入尺寸。
- 避免批量大图。
- 避免扩散式重绘、补细节、文生图能力。

如果 NAS CPU 较弱，先测试 `realesr-general-x4v3` 和 `RealESRGAN_x4plus_anime_6B`，再测试 `RealESRGAN_x4plus`、OpenModelDB 稳定模型和较新架构模型。

## 安全要求

不要直接将 Gradio 的 `7860` 端口裸露到公网。

推荐方式：

- Gradio 容器只监听本机或内网。
- nginx 反向代理到 Gradio。
- nginx 启用 HTTPS。
- nginx 增加 Basic Auth、Authelia、OAuth2 Proxy 或其他登录鉴权。
- nginx 设置合适的 `client_max_body_size`，避免超大文件拖垮服务。
- nginx 设置足够长的代理超时，避免 CPU 推理过程中连接提前断开。
- 如 Gradio 需要流式响应或 WebSocket，nginx 应保留升级相关 proxy header。
- 上传目录和输出目录不要作为公开静态目录直接暴露。
- 限制上传文件大小。
- 只允许常见图片格式，例如 PNG、JPG、JPEG、WEBP。

## 验收标准

部署完成后应满足：

- 手机浏览器可以打开 Gradio WebUI。
- 可以上传一张图片。
- 可以选择至少两个模型。
- 可以完成 4x 放大。
- 可以预览和下载放大后的图片。
- 输出目录中可以找到结果文件。
- Docker 容器重启后，模型和输出文件不丢失。
- pytest 测试通过。
- README 中写清楚启动、停止、更新、添加模型、查看日志的方法。
- README 中写清楚 nginx 反代、HTTPS、登录鉴权、上传大小限制和代理超时设置。
- README 中记录一次实际测试结果：
  - 测试图片尺寸。
  - 使用模型。
  - 推理耗时。
  - 输出尺寸。
  - 输出文件路径。

## 给 Codex 的实施说明

可以直接把下面这段作为任务交给 NAS 上的 Codex：

```text
请在这台无 GPU 的 x86 NAS 上，用 Docker Compose 部署一个自建 Gradio 图片放大 WebUI。

不要使用 ComfyUI。

目标是实现一个轻量图片超分服务：
上传图片 -> 选择模型 -> CPU 推理放大 -> 预览结果 -> 下载图片。

要求：
1. 创建 /volume1/docker/upscale-webui/ 目录结构。
2. 编写 app/Dockerfile、app/requirements.txt、app/app.py、app/inference.py、app/model_registry.py。
3. 编写 compose.yml。
4. 使用 Python + Gradio 实现 WebUI。
5. 支持 CPU-only 运行，不依赖 NVIDIA GPU/CUDA。
6. 持久化 models、input、output、logs 目录。
7. 第一批稳定基线模型优先支持 RealESRGAN_x4plus、RealESRGAN_x4plus_anime_6B、realesr-general-x4v3、4x-UltraSharp、4x-Remacri。
8. 第一阶段不做自动模型下载器，模型文件由用户手动放入 models/。
9. 模型注册表要记录 backend、architecture、scale、path、适用图片类型和备注。
10. 第一阶段真实推理优先实现 Spandrel/PyTorch CPU。
11. ONNX Runtime CPU 和 Real-ESRGAN 官方实现只预留 backend 字段和扩展点，第二阶段再实现。
12. 第二批较新架构模型预留 SPAN、RealPLKSR/PLKSR、DAT/ATD、HAT、SwinIR、OmniSR 的接入方式。
13. 模型加载要做缓存，避免每次处理重复加载。
14. 输出文件名包含时间戳、模型名和放大倍数。
15. 页面显示输入尺寸、输出尺寸、模型名、推理耗时。
16. 默认限制最大输入尺寸，避免 NAS 被大图拖死。
17. 默认使用 tiled inference，tile size 和 overlap 支持配置。
18. 不要裸露公网端口，Compose 默认绑定 127.0.0.1:7860。
19. nginx 反代、证书和登录鉴权由宿主机处理，应用不需要专门实现反代能力。
20. 写 README.md，说明启动、停止、更新、添加模型、查看日志、访问 WebUI、nginx 反代和登录鉴权的方法。
21. 添加 pytest 测试，测试使用 fake backend，不依赖真实大模型。
22. 完成后做一次实际图片放大测试，并记录测试图片尺寸、模型、耗时和输出位置。
```

## 参考资料

- Gradio 官方文档：https://www.gradio.app/docs
- Spandrel 项目：https://github.com/chaiNNer-org/spandrel
- Real-ESRGAN 官方模型表：https://github.com/xinntao/Real-ESRGAN/blob/master/docs/model_zoo.md
- Real-ESRGAN 项目：https://github.com/xinntao/Real-ESRGAN
- OpenModelDB 模型库：https://openmodeldb.info/
