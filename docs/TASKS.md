# Pixloom Task Plan

Last updated: 2026-04-30

## P0

1. Create the runtime directory structure.
   - `app/`
   - `models/`
   - `input/`
   - `output/`
   - `logs/`
   - `tests/`

2. Add Docker Compose and container build files.
   - `compose.yml` binds `127.0.0.1:7860:7860` by default.
   - `app/Dockerfile` uses a CPU-only Python base.
   - `app/requirements.txt` includes Gradio, Pillow, pytest, and first backend dependencies.

3. Implement the model registry.
   - Explicit fields: id, display name, backend, architecture, scale, path, image types, notes, enabled.
   - UI-visible model list only includes enabled models with existing files.
   - Unknown model id and missing model file return clear errors.

4. Implement inference validation and output handling.
   - Accept PNG, JPG, JPEG, WEBP.
   - Decode with Pillow before trusting the file.
   - Enforce max input and output dimensions.
   - Save uploads to `input/`.
   - Save outputs to `output/`.
   - Generate filenames with timestamp, model id, and scale.

5. Implement first CPU backend.
   - Start with Spandrel/PyTorch CPU.
   - Cache loaded models by model id and file path metadata.
   - Use tiled inference by default.
   - Return input size, output size, elapsed time, model name, and output path.
   - Use a fake backend in tests; real model validation is manual on NAS.

6. Implement Gradio UI.
   - Mobile-friendly single page.
   - Image upload.
   - Model dropdown.
   - Output format and quality controls.
   - Start button.
   - Preview result.
   - Download result.
   - Status text with model, dimensions, elapsed time, and output path.
   - Optional Gradio auth via `GRADIO_AUTH_USER` / `GRADIO_AUTH_PASS`, documented as a fallback only.

7. Add tests.
   - `tests/test_model_registry.py`
   - `tests/test_inference_validation.py`
   - `tests/test_output_paths.py`
   - `tests/test_app_handler.py`
   - Tests must cover happy paths, missing models, invalid file type, too-large image, backend failure, safe output paths, and UI handler error mapping.

8. Replace README with deployment instructions.
   - Start, stop, rebuild, update.
   - Directory layout.
   - How to place model files manually.
   - nginx reverse proxy example.
   - HTTPS and login handled by host nginx.
   - Upload size and proxy timeout settings.
   - Manual acceptance test template.

## P1

1. Add ONNX Runtime backend after the first real Spandrel model path works.
2. Add Real-ESRGAN official compatibility path only if Spandrel cannot load a required baseline model cleanly.
3. Add a model download helper only after model URLs and licenses are confirmed stable.
4. Add resource telemetry in logs: memory estimate, tile size, and per-stage timings.

## Explicitly Deferred

- Batch processing.
- GPU/CUDA/ROCm support.
- ncnn-vulkan.
- Public model downloader in v1.
- User account system inside the app.
- Docker image publishing pipeline.
- Automatic nginx configuration.
