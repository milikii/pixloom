# Pixloom Progress

Last updated: 2026-05-03

## Current Phase

Pixloom v1 is implemented. V1.1 now has a real background SQLite worker, queued
batch submission, a shorter tabbed right panel, and an expanded operator model set.
The remaining V1.1 work is broader subjective model acceptance, not queue plumbing.

V2 frontend work has begun:
- FastAPI backend under `backend/` with routers for batches, tasks, files, logs,
  models, upload, and health.
- React/Next.js SPA under `frontend/` with Gallery White design system
  (default light mode + dark mode).
- CSS design tokens completed: full color system, 4-level shadows, border-radius
  scale, semantic status colors (success/warning/info).
- All components use semantic tokens via Tailwind v4 `@theme` extensions.
- `StatusBadge` capsule component implemented (icon + color + text for every
  task status).

## Completed

- Product requirements captured in `nas-upscale-webui-requirements副本.md`.
- Architecture captured in `docs/ARCHITECTURE.md`.
- High-level tasks captured in `docs/TASKS.md`.
- Executable implementation plan captured in `docs/superpowers/plans/2026-04-30-pixloom-v1.md`.
- Chinese-first Gradio UI copy implemented.
- Model suitability guidance surfaced in the WebUI.
- Request-id based error contract implemented.
- JSONL request audit logging implemented under `logs/`.
- Thumbnail history implemented for successful outputs.
- History deletion removes linked local input/output images when paths are safe.
- Optional retention cleanup added and disabled by default.
- Trellis backend and frontend spec files filled based on the real codebase.
- `PIXLOOM_DB_PATH` added with default `state/pixloom.sqlite3`.
- SQLite `batches` and `tasks` tables added in `app/tasks.py`.
- Existing single-image upscale flow now enqueues, claims, completes, or fails a
  task row while preserving the current UI return shape.
- Multi-image uploads now create one batch with one task per image and process
  sequentially.
- One failed image in a batch no longer aborts the remaining images.
- The WebUI task list now reads from SQLite and shows completed, failed, deleted,
  interrupted, queued, and running statuses.
- Task deletion removes only safe linked runtime files, marks the task deleted,
  and logs `task_deleted`.
- Startup marks stale `running` tasks as `interrupted`.
- Compose persists `state/` as `/data/state`.
- Runtime model exposure now distinguishes locally installed evaluation models from
  operator-visible accepted models.
- The default dropdown now exposes a 7-model operator set:
  Remacri, RealESRGAN x4 Photo, UltraSharp, Anime 6B, General v3, HAT-L 4x, and
  Real-CUGAN 3x denoise.
- The local model pool is now expanded beyond the initial two operator-visible models
  to a 16-file local inventory (~1.5G), including RealESRGAN x4 Photo, Remacri,
  UltraSharp, NMKD-Siax, CodeFormer, GFPGAN, RealPLKSR, DAT, SPAN, Real-CUGAN,
  Omni-SR, APISR, and related evaluation weights for further integration work.
- Completed one local runtime smoke matrix against all currently tracked registry
  entries. Most Spandrel-path weights load and run on a tiny sample image; ONNX,
  face-restoration, and custom-runtime models remain blocked on backend work, and one
  OmniSR DF2K weight still errors on the current path.
- Completed a first real-image runtime pass for:
  - `Remacri`
  - `RealESRGAN x4 Photo`
  - `UltraSharp`
  - `NMKD-Siax`
  - `SPAN`
  - `RealPLKSR`
  - `DAT`
  These now have real output files under `output/`, not just tiny smoke results.
- Reclassified `DAT`, `HAT`, and heavier OmniSR-style weights as long-run CPU
  candidates rather than short interactive acceptance checks.
- Batch queue intake now persists inputs first and writes batch/task rows atomically
  so setup failures do not leave half-created queued work.
- Batch submission now returns after enqueue and is processed by one in-process
  background worker that claims queued SQLite rows serially.
- The WebUI right column is now split into `结果`, `任务`, and `日志` tabs, and the
  task view auto-refreshes from SQLite instead of forcing the operator to babysit one
  long sidebar.
- The Gradio surface was restyled into a denser operator console with a status
  header, restrained light panels, clearer section hierarchy, and a collapsed
  completed-image area so the mobile viewport does not start with an overlong task
  column.
- Running tasks now persist progress stage and percentage into SQLite so the UI can
  show live progress and ETA estimates while the background worker is still running.
- Mobile submission controls are shortened further by folding model guidance and
  output settings into accordions instead of leaving every control expanded.
- Real-CUGAN now runs through the current Spandrel path, and HAT-L is exposed as a
  slow operator-visible option with an explicit CPU warning.
- Added regression coverage for accepted-only model visibility, no-operator-ready
  guidance, background queue processing, and batch queue setup failure cleanup.
- FastAPI backend scaffolded with routers for batches (POST), tasks (GET/DELETE),
  files (GET input/output), logs (GET by request_id), models (GET guidance), upload
  (POST), and health (GET). API reuses existing `app/` modules directly.
- React/Next.js SPA scaffolded with domain-split component tree: shell (ShellHeader,
  PanelHead, ThemeToggle), submission (UploadZone, ModelPicker, ModelGuidance,
  OutputParams, SubmitButton), tasks (TaskPanel, TaskDetail, StatusBadge), results
  (ResultsTabs), and logs (RequestLogs).
- Design system CSS tokens implemented in `frontend/src/app/globals.css`: full light
  and dark color palettes, success/warning/info semantic colors with subtle variants,
  4-level shadow system (card rest/hover, button glow, modal), border-radius scale
  (xs/sm/md/lg/full).
- Theme switching via `next-themes` with `class` attribute, default light mode,
  system preference support, and hydration-mismatch mount guard.
- All components refactored to reference semantic tokens exclusively; zero hardcoded
  Tailwind palette colors remain.
- TypeScript noEmit and ESLint pass clean.

## Verification

- `python3 -m compileall app tests`: passed
- `.venv/bin/pytest -q tests/test_config.py tests/test_history.py tests/test_inference_validation.py tests/test_app_handler.py`: passed (`30 passed`)
- `.venv/bin/pytest -q tests/test_app_handler.py tests/test_inference_validation.py tests/test_spandrel_backend.py`: passed (`23 passed`)
- `.venv/bin/pytest -q`: passed (`49 passed`)
- `docker run --rm -v "$PWD:/workspace" -w /workspace pixloom-upscale-webui python -m pytest -q`: passed (`43 passed`)
- `docker compose build`: passed
- `docker compose up -d --force-recreate`: passed
- Container is currently publishing `0.0.0.0:7860->7860/tcp`
- 2026-05-01 V1.1 queue slice:
  - `.venv/bin/python -m compileall app tests`: passed
  - `.venv/bin/pytest -q tests/test_config.py tests/test_tasks.py tests/test_app_handler.py tests/test_inference_validation.py`: passed (`33 passed`)
  - `.venv/bin/pytest -q`: passed (`56 passed`)
- 2026-05-01 V1.1 batch/task-list slice:
  - `.venv/bin/python -m compileall app tests`: passed
  - `.venv/bin/pytest -q tests/test_tasks.py tests/test_app_handler.py`: passed (`17 passed`)
  - `.venv/bin/pytest -q`: passed (`60 passed`)
  - `docker compose build`: passed
  - `docker compose up -d --force-recreate`: passed
  - `docker exec pixloom-upscale-webui python -c "...urllib.request..."`: passed (`200`)
- 2026-05-01 V1.1 model-matrix / launch-set slice:
  - `.venv/bin/pytest -q tests/test_model_inventory.py tests/test_model_registry.py tests/test_app_handler.py tests/test_tasks.py`: passed (`32 passed`)
  - `.venv/bin/pytest -q`: passed (`72 passed`)
- 2026-05-01 queue-worker / UI compression slice:
  - `python3 -m py_compile app/app.py app/model_registry.py app/model_inventory.py app/model_matrix.py app/tasks.py`: passed
  - `.venv/bin/pytest -q tests/test_model_registry.py tests/test_app_handler.py tests/test_tasks.py tests/test_model_inventory.py`: passed (`35 passed`)
  - local runtime spot checks:
    - `hat-l-4x` tiny sample: passed (`32x24`, `2.984s`)
    - `real-cugan-up3x-denoise3x` tiny sample: passed (`24x18`, `0.061s`)
- 2026-05-03 V2 design-system / semantic-token slice:
  - `npx tsc --noEmit`: passed (zero errors)
  - `npx eslint src/`: passed (zero errors, zero warnings)
  - `python3 -m py_compile app/app.py app/tasks.py tests/test_app_handler.py tests/test_tasks.py`: passed
  - `.venv/bin/pytest -q`: passed (`77 passed`)

## Pixloom V1 Runtime Smoke Test

- `docker compose build`: passed
- `docker compose up -d --force-recreate`: passed
- LAN host port publishing: configured for `7860:7860`
- Gradio startup log: confirmed on `0.0.0.0:7860`

## Pixloom V1 Real Model Acceptance

- Date: 2026-04-30
- Input size: 1402x1122
- Model: Real-ESRGAN 4x Anime
- Output size: 5608x4488
- Elapsed time: 92.11s
- Output path: output/20260430-031033-809102_image-dabc1f26-17ef-4e44-91e9-2b55b44c6da0-0_realesrgan-x4plus-anime_4x.png
- Phone browser preview: pending manual browser check
- Download: pending manual browser check
- Container restart persistence: passed for runtime directories; output file written successfully under `output/`

## Remaining Manual Checks

Use `docs/V1_1_ACCEPTANCE_CHECKLIST.md` as the source of truth for the next real
phone/NAS acceptance pass. The automated parts (smoke matrix, real-image outputs for
7 operator models + 4 evaluation models, code contract audit, batch-safety audit) are
complete. Remaining purely manual steps:

- Confirm the Chinese-first UI renders as expected from a real phone browser.
- Trigger one controlled failure in the WebUI and confirm the request id appears and matches a row in `logs/`.
- Confirm model guidance text is understandable on a narrow mobile viewport.
- Submit one real batch from a phone and confirm `state/pixloom.sqlite3` contains
  one batch id with multiple task rows.
- Submit one real partial batch and confirm success/failure counts are obvious in the
  returned status text and task list.
- Confirm at least one locally present but unapproved model stays out of the primary
  dropdown.
- Delete one completed task from the WebUI and confirm only the linked input/output
  files are removed.

## Closure Decision (2026-05-03)

Keep the current small accepted launch set of 7 operator-visible models:

1. `照片自然 - 4x Remacri`
2. `照片通用 - Real-ESRGAN 4x`
3. `锐化插画 - 4x UltraSharp`
4. `动漫插画 - Real-ESRGAN Anime 6B`
5. `快速试跑 - Real-ESRGAN General v3`
6. `质量上限 - HAT-L 4x`
7. `动漫修复 - Real-CUGAN 3x 去噪`

The broader 16-file evaluation pool (NMKD-Siax, SPAN, RealPLKSR, DAT, OmniSR,
CodeFormer, GFPGAN, APISR) has smoke-test results and real-image outputs for
candidate models, but none have been promoted into the operator set. The exposure
contract is enforced at two layers: `list_available_models()` at the UI boundary
and `resolve_model()` at the worker boundary. Batch-ingest failure safety is
verified through SQLite transactions with immediate rollback and input cleanup.

Additional evaluation models (ONNX, face-restoration, custom-runtime) remain
blocked on backend work and stay in the evaluation pool.

The launch set will be re-evaluated after the manual phone/NAS acceptance pass.
