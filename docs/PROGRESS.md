# Pixloom Progress

Last updated: 2026-05-08

## Current Phase

Pixloom has moved to a single production surface: React/Next.js static frontend
served by FastAPI from one Docker container on port `7860`.

The legacy Gradio entrypoint has been removed. Shared runtime modules under `app/`
remain because FastAPI and the worker use them for config, model registry,
inference, SQLite tasks, history cleanup, and request logging.

## Completed

- FastAPI backend under `backend/` with routers for models, upload, batches, tasks,
  files, logs, and health.
- React/Next.js SPA under `frontend/` with Chinese-first operator flow.
- Next static export configured for production.
- Root multi-stage `Dockerfile` builds frontend assets and copies them into the
  Python runtime image.
- `compose.yml` now defines one `pixloom` service and publishes `7860:7860`.
- FastAPI mounts the built frontend export when `PIXLOOM_FRONTEND_DIST` exists.
- Gradio-specific files and configuration were removed:
  - `app/app.py`
  - `app/Dockerfile`
  - `app/requirements.txt`
  - `compose.override.yml`
  - `GRADIO_*` config handling
- SQLite task queue remains the source of truth for queued/running/completed/failed/
  deleted/interrupted work.
- Output size presets now let operators keep native model scale or target 2K, 4K,
  or 8K by final longest side while preserving aspect ratio.
- Background worker failure handling marks unsupported-backend tasks as failed
  instead of leaving them stuck as running.
- APISR, CodeFormer, and GFPGAN now have ONNX/custom backend paths and are part of
  the operator-visible installed model set when their files are present.
- Batch pre-queue validation failures now return structured 4xx errors, write
  `ui_rejected` audit rows, and surface Chinese request-id messages in the SPA.
- The task panel keeps the selected result preview visible above the task list so
  clicking a task immediately updates the visible output; request logs stay in the
  same panel and partial batch completion remains highlighted.
- Frontend/backend execution guidance updated so future agents target React/FastAPI.

## Verification To Run For This Slice

- `.venv/bin/pytest -q`
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- `docker compose build`
- optional runtime smoke:
  - `docker compose up -d`
  - `curl http://localhost:7860/api/health`
  - open `http://localhost:7860`

## Current Operator Model Policy

The API reports installed model files, the current operator-visible set, and hidden
evaluation-only files separately. The exposure contract is enforced at two layers:

- `list_available_models()` at the API/UI boundary
- `resolve_model()` at the worker boundary

The current operator-visible set intentionally keeps all usable local models exposed:

1. `SPAN 4x`
2. `RealPLKSR 4x`
3. `照片修复 - 4x NMKD-Siax`
4. `锐化插画 - 4x UltraSharp`
5. `DRCT 4x`
6. `质量上限 - HAT-L 4x`
7. `DRCT-L 4x`
8. `APISR 4x`
9. `动漫修复 - Real-CUGAN 3x 去噪`
10. `动漫精修 - Real-CUGAN 2x 去噪`
11. `动漫插画 - Real-ESRGAN Anime 6B`
12. `CodeFormer`
13. `GFPGAN v1.4`
14. `快速试跑 - Real-ESRGAN General v3`
15. `照片自然 - 4x Remacri`
16. `照片通用 - Real-ESRGAN 4x`

The current hidden evaluation-only tracked model is `DAT2 4x 预训练版`. It remains
installed for comparison but outside the main submission flow because it is a pretrain
research artifact.
