# Pixloom Task Plan

Last updated: 2026-05-03

## P0

1. Create the runtime directory structure.
   - `app/`
   - `models/`
   - `input/`
   - `output/`
   - `logs/`
   - `tests/`

2. Add Docker Compose and container build files.
   - `compose.yml` publishes `7860:7860` for trusted LAN access by default.
   - `app/Dockerfile` uses a CPU-only Python base.
   - `app/requirements.txt` includes Gradio, Pillow, pytest, and first backend dependencies.

3. Implement the model registry.
   - Explicit fields: id, display name, backend, architecture, scale, path, image types, notes, enabled.
   - Add user-facing guidance fields for the WebUI: Chinese recommendation text and best-fit image types.
   - UI-visible model list only includes enabled models with existing files.
   - Unknown model id and missing model file return clear errors.

4. Implement inference validation and output handling.
   - Accept PNG, JPG, JPEG, WEBP.
   - Decode with Pillow before trusting the file.
   - Enforce max input and output dimensions.
   - Save uploads to `input/`.
   - Save outputs to `output/`.
   - Generate filenames with timestamp, model id, and scale.
   - Assign a request id to each upscale attempt.
   - Emit structured JSONL logs to `logs/` for success and failure paths.

5. Implement first CPU backend.
   - Start with Spandrel/PyTorch CPU.
   - Cache loaded models by model id and file path metadata.
   - Use tiled inference by default.
   - Return input size, output size, elapsed time, model name, and output path.
   - Use a fake backend in tests; real model validation is manual on NAS.

6. Implement Gradio UI.
   - Mobile-friendly single page.
   - Chinese-first labels, helper text, status text, and error text.
   - Image upload.
   - Model dropdown.
   - Model guidance area that explains which model fits what kind of image.
   - Output format and quality controls.
   - Start button.
   - Preview result.
   - Download result.
   - Thumbnail history for recent successful outputs.
   - Delete selected history item and remove linked local input/output images.
   - Status text with model, dimensions, elapsed time, output path, and request id.
   - Actionable failure box with likely cause and next action.
   - Optional Gradio auth via `GRADIO_AUTH_USER` / `GRADIO_AUTH_PASS`, documented as a fallback only.

7. Add tests.
   - `tests/test_model_registry.py`
   - `tests/test_inference_validation.py`
   - `tests/test_output_paths.py`
   - `tests/test_app_handler.py`
   - Tests must cover happy paths, missing models, invalid file type, too-large image, backend failure, safe output paths, UI handler error mapping, request-id log correlation, and Chinese user-facing copy for key failure states.

8. Replace README with deployment instructions.
   - Start, stop, rebuild, update.
   - Directory layout.
   - How to place model files manually.
   - nginx reverse proxy example.
   - HTTPS and login handled by host nginx.
   - File retention behavior for `input/`, `output/`, and `logs/`.
   - History deletion and optional retention cleanup behavior.
   - Upload size and proxy timeout settings.
   - Manual acceptance test template.

## P1

1. Add ONNX Runtime backend after the first real Spandrel model path works.
2. Add Real-ESRGAN official compatibility path only if Spandrel cannot load a required baseline model cleanly.
3. Add a model download helper only after model URLs and licenses are confirmed stable.
4. Extend logs with resource telemetry: memory estimate, tile size, and per-stage timings.
5. Add a dry-run cleanup command if operators need a CLI preview before enabling retention cleanup.

## V1.1 Queue / Batch / Model Plan

1. Durable single-image task queue.
   - [x] Add `PIXLOOM_DB_PATH` and `state/` persistence.
   - [x] Add SQLite `batches` and `tasks` tables.
   - [x] Enqueue, claim, complete, fail, list, and interrupt task records.
   - [x] Route the existing single-image handler through the queue without changing the visible flow.
   - [x] Run queued work from one in-process background worker instead of keeping the browser callback busy.
   - [x] Cover config, task store, and UI handler behavior with pytest.

2. Multi-image batch UI.
   - [x] Accept multiple uploaded images in one submission.
   - [x] Store one `batch_id` with per-image `request_id`s.
   - [x] Process valid images sequentially so one failure does not abort the rest.
   - [x] Show batch summary in Chinese.

3. Task list UI.
   - [x] Replace or evolve thumbnail history into queued/running/completed/failed/interrupted task views.
   - [x] Let completed tasks preview/download when output still exists.
   - [x] Show failed task error code, request id, and next-step summary.
   - [x] Delete task rows safely by resolving input/output paths under runtime directories.
   - [x] Split the right column into shorter result/task/log sections and auto-refresh task state from SQLite.

4. Model configuration polish.
   - [x] Add clearer CPU-friendly model recommendations.
   - [x] Distinguish natural photo, sharp web image, anime/illustration, and quick-test choices.
   - [x] Keep heavy or unverified architectures disabled until tested locally, unless the user explicitly promotes a slow specialist model.
   - [x] Keep operator-facing dropdown limited to locally accepted models.
   - [x] Complete local acceptance matrix for the broader downloaded evaluation pool.

## Explicitly Deferred

- Parallel batch processing.
- GPU/CUDA/ROCm support.
- ncnn-vulkan.
- Public model downloader in v1.
- User account system inside the app.
- Docker image publishing pipeline.
- Automatic nginx configuration.
