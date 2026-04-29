# Pixloom Architecture

Last updated: 2026-04-30

## Goal

Pixloom is a self-hosted NAS image upscaling WebUI. The first release must let a phone browser upload one image, choose a model, run CPU-only upscaling, preview the output, and download the result.

This is not a ComfyUI replacement and not a model workflow editor. The first release optimizes for a small, boring, verifiable NAS service.

## Engineering Decision

Use the minimum service shape that can run on an x86 NAS:

```text
phone browser
  -> nginx on NAS host
     -> http://127.0.0.1:7860
        -> Gradio app in Docker
           -> model registry
           -> CPU inference backend
           -> persisted input/output/log folders
```

The application does not own public HTTPS, certificates, or login. Those stay in host nginx. The app only exposes an internal HTTP service.

## Runtime Layout

```text
repo/
  compose.yml
  app/
    Dockerfile
    requirements.txt
    app.py
    inference.py
    model_registry.py
  models/
  input/
  output/
  logs/
```

Default Compose port binding:

```yaml
ports:
  - "127.0.0.1:7860:7860"
```

Gradio listens inside the container on `0.0.0.0:7860`. Docker publishes it only to host loopback by default.

## Data Flow

```text
Upload image
  |
  v
Validate format + size
  |-- invalid format/too large -> clear UI error
  |
  v
Persist original to input/
  |
  v
Resolve selected model from registry
  |-- missing file/unsupported backend -> clear UI error
  |
  v
Load cached model
  |-- first use: load from models/
  |-- later use: reuse cached descriptor/session
  |
  v
Run CPU tiled inference
  |-- inference error/OOM -> clear UI error + log
  |
  v
Persist result to output/
  |
  v
Return preview + download file + status metadata
```

## Backend Scope

First implementation should include:

- `spandrel` / PyTorch CPU as the first real model backend.
- A model registry that can describe future `onnxruntime` and `realesrgan` entries without implementing every backend now.
- Manual model placement in `models/` for v1. No automatic downloader in the first pass.
- CPU tiled inference from the start, with configurable tile size and overlap.

Rationale:

- Spandrel matches the `.pth` / `.safetensors` model ecosystem better than starting with ONNX only.
- ONNX Runtime CPU is a good later backend, but it requires ONNX model availability and per-model tensor conventions.
- A downloader adds URL churn, license ambiguity, and failure modes that do not block the first usable NAS service.
- Full-frame CPU inference can run out of memory on NAS hardware; tiling is part of the first usable version, not polish.

## Model Registry Contract

Each model entry should be explicit:

```text
id
display_name
backend
architecture
scale
path
image_types
notes
enabled
```

The UI should show only enabled models whose files exist. Missing model files should produce a readable warning in the UI or README, not a stack trace.

## Security Boundary

Application responsibilities:

- Validate image extensions and decoded image type.
- Enforce max input and output dimensions.
- Save uploads only under `input/`.
- Save outputs only under `output/`.
- Avoid exposing `input/` and `output/` as a public static directory.
- Show clear errors without dumping secrets or full tracebacks into the UI.

Host nginx responsibilities:

- HTTPS certificate.
- Public hostname.
- Basic Auth, Authelia, OAuth2 Proxy, or existing unified login.
- Upload body size limit.
- Proxy timeout long enough for CPU inference.
- WebSocket/streaming-safe proxy headers if Gradio needs them.

## Test Plan

No test framework exists yet. Add `pytest` with unit tests for pure logic and lightweight integration tests that do not require real model downloads.

```text
CODE PATHS                                      USER FLOWS
[+] app/model_registry.py                       [+] Phone upload flow
  ├── [GAP] list enabled models                   ├── [GAP] upload valid image
  ├── [GAP] hide missing model files              ├── [GAP] choose model
  └── [GAP] reject unknown model id               ├── [GAP] run upscale
                                                  └── [GAP] download output

[+] app/inference.py                            [+] Error states
  ├── [GAP] validate image format                 ├── [GAP] unsupported file
  ├── [GAP] enforce max input size                ├── [GAP] too-large image
  ├── [GAP] generate safe output filename         ├── [GAP] missing model file
  ├── [GAP] cache loaded model                    └── [GAP] backend failure
  ├── [GAP] tiled inference path
  └── [GAP] backend exception path

[+] app/app.py
  ├── [GAP] Gradio handler returns preview/file/status
  ├── [GAP] handler maps known errors to UI messages
  └── [GAP] auth env vars optional, not required

COVERAGE TARGET: all planned branches covered before ship.
```

Recommended test files:

- `tests/test_model_registry.py`
- `tests/test_inference_validation.py`
- `tests/test_output_paths.py`
- `tests/test_app_handler.py`

Use a fake backend in tests so CI/local tests do not need large model files. Real model testing should be a documented manual acceptance test on the NAS.

## Performance Risks

- CPU inference is slow. The UI must show elapsed time and not imply interactive speed.
- Large input images can exhaust memory. Enforce max dimensions before inference.
- Full-frame model execution can exhaust memory even if the input passes validation. Use tiled inference by default.
- Model load time is high. Cache loaded models by model id and path metadata.
- Concurrent requests can overload NAS CPU. Keep Gradio concurrency low for v1, ideally one inference at a time.

## NOT In Scope

- ComfyUI-style workflow graph.
- Batch processing.
- Public model downloader.
- GPU/CUDA/ROCm support.
- ncnn-vulkan acceleration.
- User account system inside the app.
- CI image publishing or registry release.
- Automatic nginx configuration.

## What Already Exists

- `nas-upscale-webui-requirements副本.md` contains the product requirements and model list.
- `README.md` is only a placeholder and should be replaced with deployment instructions.
- No app code exists yet, so there is no existing implementation to reuse.

## Parallelization

Sequential implementation is recommended for v1. The same small set of modules (`app/`, `compose.yml`, README) is touched by every step, so parallel worktrees would create more coordination than speed.

## Source Notes

- Gradio supports `server_name`, `server_port`, and optional `auth` on `Blocks.launch`.
- Docker Compose `ports` supports host IP binding; omitting host IP binds to all interfaces.
- ONNX Runtime has a CPU Python package and `InferenceSession` execution providers.
- Spandrel loads PyTorch super-resolution models and supports many SR architectures, but its README states it does not yet provide complete easy inference code.
