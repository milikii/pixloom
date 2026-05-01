<!-- /autoplan restore point: /root/.gstack/projects/milikii-pixloom/pixloom-v1-implementation-autoplan-restore-20260501-010119.md -->
# Pixloom V1.1 Task Queue, Batch Upload, And Model Configuration Plan

## Goal

Turn Pixloom from a single-image upscaler with thumbnail history into a small NAS job
console: the operator can submit one image or many images, see queued/running/done/failed
tasks, return later from a phone, and choose models that fit the actual CPU-only hardware.

## Current State

- The Gradio app already supports one uploaded image per run.
- `demo.queue(default_concurrency_limit=1)` already serializes inference work.
- Successful outputs are rebuilt as history thumbnails from append-only JSONL logs and
  existing files under `output/`.
- Deleting a history item removes its linked stored input and output when both paths are
  safe children of the configured runtime directories.
- Current installed models are:
  - `RealESRGAN_x4plus_anime_6B.pth`
  - `realesr-general-x4v3.pth`
- Current pain: those two models skew sharp or lightweight. They are useful baselines but
  not a complete operator-facing model set for photos, illustrations, and softer natural
  output.

## Premises To Confirm

1. The NAS remains CPU-only for this release: Intel Core i7-8700, 6 cores / 12 threads,
   32 GB RAM, 1 TB SSD.
2. The product should stay a simple Gradio WebUI, not a ComfyUI workflow editor.
3. Batch work should be sequential by default, because parallel CPU inference would make
   the NAS slow for every user and increase memory pressure.
4. "History" should become a task list. JSONL logs remain the audit trail, but task state
   should move to SQLite so the operator can safely return later.
5. The first useful batch version does not need resumable browser uploads, user accounts,
   GPU support, or automatic model downloads.

## Proposed Product Shape

### Operator Flow

```text
phone browser
  -> upload one image OR multiple images
  -> choose model, output format, quality
  -> submit as one task batch
  -> task list shows:
       queued
       running
       completed
       failed
       deleted
  -> select any task to preview output, download output, inspect logs, or delete files
```

### UI Structure

- Rename `历史记录` to `任务列表`.
- Add two sections:
  - `排队 / 处理中`: queued and running tasks.
  - `已完成 / 失败`: completed and failed tasks.
- Keep result preview and download on the right side.
- Add one upload control that accepts multiple files when the operator wants batch work.
- Keep single-image usage as the same flow with one selected file.
- Show a batch summary after submit:
  - total images
  - accepted images
  - rejected images
  - batch id
  - expected serial processing note
- Each task row/card should show:
  - status
  - request id
  - batch id
  - input filename
  - model
  - created time
  - started time
  - completed time
  - elapsed seconds
  - output thumbnail when available
  - Chinese error summary when failed

## Engineering Approach

### Data Model

Add `PIXLOOM_DB_PATH` and a small SQLite task queue. JSONL stays append-only audit;
SQLite becomes the task list and queue source of truth.

```text
batch_id
request_id
task_status: queued | running | completed | failed | deleted | pruned
event: task_queued | request_started | inference_started | request_succeeded |
       request_failed | task_deleted | history_pruned
input_filename
input_path
output_path
model_id
created_at
started_at
completed_at
elapsed_seconds
error_code
error_detail
```

`request_id` remains the per-image trace id. `batch_id` groups images submitted together.
SQLite tables:

```text
batches(id, created_at, model_id, output_format, quality, total_count)
tasks(request_id primary key, batch_id, status, input_filename, input_path, output_path,
      model_id, output_format, quality, created_at, started_at, completed_at,
      elapsed_seconds, error_code, error_detail, retry_of_request_id)
```

Use Python stdlib `sqlite3`. Keep writes small and explicit; no ORM.

### Queue Execution

Use a minimal durable SQLite queue for v1.1:

- Keep `default_concurrency_limit=1` for UI event handlers.
- Submit persists each accepted upload to `input/`, inserts a queued task row, logs
  `task_queued`, and returns immediately with a batch summary.
- An in-process single worker loop claims queued rows and calls the existing `run_upscale`
  once per task.
- The worker updates task status before and after inference: `queued -> running ->
  completed` or `failed`.
- Continue processing later images when one image fails.
- On app startup, any task left as `running` becomes `interrupted` with a visible retry
  action. Queued tasks can be processed after restart because their inputs were already
  persisted and stored in SQLite.

This is still not a full external worker service. It is a small in-process worker backed
by SQLite state, which matches the current NAS deployment while supporting the core
"submit now, come back later" operator promise.

### Task List Reconstruction

Replace `app/history.py` with `app/tasks.py`, or keep `history.py` as a compatibility
wrapper and move new logic into `tasks.py`.

Task listing should be read from SQLite, with JSONL used for request log detail:

- successful tasks with existing outputs can preview/download
- failed tasks remain visible with error code and request id even without an output
- interrupted tasks remain visible with a retry action

### Deletion And Retention

- Delete one task: remove linked input/output files safely and log `task_deleted`.
- Delete batch: remove all tasks in the batch after confirmation.
- Retention cleanup should apply to completed outputs and stored inputs, not to logs.
- Failed tasks should remain in logs but have no image files to delete unless an input was
  persisted before failure.

### Tests

Add or update tests for:

- task listing from queued/running/success/failure/interrupted/deleted SQLite rows
- queue claim behavior uses a transaction so two workers cannot claim the same task
- batch id grouping
- single-image submit still works
- multi-image submit processes valid images and records failures without aborting the batch
- failed task appears in task list with Chinese error fields
- delete task deletes only safe input/output paths
- stale queued/running tasks after restart are visible as interrupted
- Gradio handler return shape for batch summaries and task list updates

## Model Configuration Plan

### Baseline Recommendation For i7-8700 / 32 GB RAM

Configure a small, opinionated model set. Do not expose every famous model immediately.

| Priority | Model | Backend now | Purpose | Recommendation |
|---|---|---|---|---|
| P0 | `4x_foolhardy_Remacri.pth` | Spandrel | Natural-looking photos / mixed images | Add as the default natural-photo recommendation because current outputs feel too sharp. |
| P0 | `RealESRGAN_x4plus.pth` | Spandrel | General photos | Add as the stable official photo baseline. Less specialized than current anime/general-v3 pair. |
| P0 | `4x-UltraSharp.pth` | Spandrel | AI art / compressed web images / crisp illustrations | Keep available but label as sharp style, not default for portraits. |
| P0 | `RealESRGAN_x4plus_anime_6B.pth` | Spandrel | Anime / illustrations | Keep installed and label clearly as anime-oriented. |
| P0 | `realesr-general-x4v3.pth` | Spandrel | Fast test / weaker CPU fallback | Keep installed as fast fallback, with lower quality expectations. |
| P1 | `4x_NMKD-Siax_200k.pth` or closest verified Siax variant | Spandrel | Noisy/compressed source | Add only after source/license/file naming are confirmed. |
| P1 | `Real-CUGAN` | Spandrel or separate backend | Anime line preservation | Evaluate after current batch queue lands; may require extra architecture/runtime checks. |
| P2 | `SPAN` / `RealPLKSR` | Spandrel if compatible | Lightweight newer candidates | Keep disabled until CPU timings and model files are verified locally. |
| P2 | CodeFormer / GFPGAN | Separate face restoration feature | Portrait face repair | Do not add to the core model dropdown yet; it changes the product from upscaling to restoration. |
| Defer | HAT / DAT / Omni-SR | Spandrel-compatible but heavy | Research-quality ceiling | Do not expose on CPU NAS by default; likely too slow for the operator workflow. |

### Default UI Guidance

- `照片自然`: Remacri, then RealESRGAN_x4plus.
- `照片锐一点 / 网图`: UltraSharp.
- `动漫插画`: RealESRGAN anime 6B first; evaluate Real-CUGAN later.
- `快速试跑`: realesr-general-x4v3.
- `人脸修复`: not available in this dropdown yet; future dedicated option after separate testing.

### Runtime Defaults

- Keep one concurrent inference.
- Keep tile size `256` as safe default.
- Allow `512` as an advanced setting after manual timing if memory stays stable.
- Keep `PIXLOOM_MAX_INPUT_SIDE=2048` and `PIXLOOM_MAX_OUTPUT_SIDE=8192` for first queue release.
- Warn that batch processing multiplies total time; it does not make CPU inference faster.

## Not In Scope

- Parallel inference.
- External worker service or Redis-style queue.
- Resumable uploads.
- Automatic model downloader.
- NCNN backend.
- Face restoration pipeline.
- Video upscaling.
- 8x direct model path.
- Public internet auth changes.

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|----------|
| 1 | Intake | Create a separate v1.1 plan instead of rewriting v1 | Mechanical | Explicit over clever | v1 already tracks the single-image release; queue/batch/model config is a new scope. | Mutating the existing v1 implementation plan |
| 2 | Product | Treat history as a task list with statuses | Mechanical | Choose completeness | The user needs queued and completed work, not only output thumbnails. | Keeping thumbnail-only history |
| 3 | Engineering | Use SQLite task queue plus one in-process worker | Taste | Choose completeness | Browser-owned batch contradicts the phone submit-and-return-later promise; user selected the more durable SQLite path. | Long foreground batch request or filesystem manifests |
| 4 | Models | Add Remacri and RealESRGAN_x4plus before chasing newer architectures | Mechanical | Explicit over clever | They fit current Spandrel/PyTorch path and address the current over-sharp output complaint. | Making SPAN/Real-CUGAN/HAT the first model expansion |
| 5 | Engineering | Keep JSONL as audit, not task state source of truth | Mechanical | Explicit over clever | Append-only logs are good for support but weak for current mutable task status. | Reconstructing live queue state only from JSONL |
| 6 | User override | Include CodeFormer/GFPGAN, HAT/DAT/OmniSR, Real-CUGAN, SPAN, and RealPLKSR in model pull-and-test scope | User Challenge | User decision | User explicitly wants the broader model evaluation despite added time, disk, and compatibility risk. | Keeping these as deferred only |

## GSTACK REVIEW REPORT

### Phase 1: CEO Review

Premises accepted with two corrections: a real task list implies persisted task state,
and user selected SQLite over filesystem manifests. The original foreground batch loop
was rejected because it would fail the operator promise when a phone tab, LAN connection,
or reverse proxy drops.

Dream state:

```text
CURRENT
  single image -> one live request -> success thumbnail history

THIS PLAN
  single/multiple upload -> SQLite queue -> one CPU worker -> task list

12-MONTH IDEAL
  model readiness, timing matrix, durable queue, optional downloader, optional face/video tracks
```

What already exists:

| Sub-problem | Existing code to reuse |
|---|---|
| One-image inference | `app/inference.py::run_upscale` |
| CPU tiled backend | `app/spandrel_backend.py::SpandrelBackend` |
| Request ids and JSONL logs | `app/request_logging.py` |
| Safe deletion and retention patterns | `app/history.py` |
| Model metadata and Chinese guidance | `app/model_registry.py` |
| Serial Gradio execution limit | `app/app.py::main` with `demo.queue(default_concurrency_limit=1)` |

NOT in scope:

- SQLite or external worker service.
- Parallel CPU inference.
- Automatic model downloads.
- Face restoration as part of the core upscaler dropdown.
- NCNN migration before current PyTorch/Spandrel path is measured.

Error & Rescue Registry:

| Failure | User-visible rescue |
|---|---|
| Browser disconnect during batch | Task manifests persist; queued tasks continue or running task becomes interrupted with retry. |
| One image fails in batch | Mark that task failed, continue later tasks, show Chinese error and request id. |
| App restarts mid-task | Mark `running` manifests as `interrupted`; keep input path for retry. |
| Missing model file | Show model readiness status with exact expected filename. |
| Output too large | Keep current max output validation and show suggested size/model action. |

### Phase 2: Design Review

UI scope detected. Design score: 7/10 after the durable queue correction.

Design decisions:

- Primary status labels should be plain Chinese: `等待中`, `处理中`, `已完成`, `失败`,
  `已中断`, `已删除`.
- Keep request id, batch id, path, and log excerpts behind `排查信息`; do not put them in
  every top-level card.
- Show two task groups first: `排队 / 处理中` and `已完成 / 失败`.
- A selected task owns the preview, download, error, log excerpt, retry, and delete actions.
- Add a model readiness panel listing present/missing files before operators hit failures.

### Phase 3: Engineering Review

Architecture:

```text
Gradio UI
  -> submit task(s)
     -> persist uploads under input/
  -> insert SQLite queued task row
     -> append JSONL task_queued
  -> task list reads SQLite

Single in-process worker
  -> claims queued SQLite task in transaction
  -> calls run_upscale()
  -> updates manifest
  -> appends JSONL request events

Preview/delete/retry
  -> task manifest
  -> safe input/output path helpers
  -> JSONL audit trail
```

Test diagram:

| Code path / flow | Test coverage required |
|---|---|
| SQLite schema init and migrations | Unit tests in new `tests/test_tasks.py` |
| Atomic queue claim | Unit tests in new `tests/test_tasks.py` |
| Queued to running to completed | Unit test with fake backend |
| Failure continues next batch item | Handler test with one failing fake service |
| Restart with running task | Unit test marks `running` as `interrupted` |
| Delete single task | Safe path deletion test adapted from history tests |
| Delete batch | Batch grouping and multiple safe deletes |
| Retry interrupted/failed task | Manifest transition and service call test |
| Model readiness | Registry/UI handler test for present/missing files |

Performance notes:

- Batch processing improves operator time, not CPU time.
- Keep one worker. Parallel inference on i7-8700 risks UI stalls and memory pressure.
- Keep tile size 256 as default; expose 512 only after a real timing/memory matrix.

### Phase 3.5: DX Review

DX scope detected because deployment docs and model placement are operator/developer-facing.
DX score: 7/10.

Required docs updates:

- README: explain task queue behavior, interrupted task recovery, model readiness, and
  manual model placement.
- `.env.example` / Compose: add `PIXLOOM_DB_PATH`.
- Manual acceptance: batch of 3 images, one failure case, app restart during queued/running
  task, delete/retry behavior.

### Dual Voice Notes

Codex CLI ran after sandbox escalation. Key finding accepted: browser-owned batch is not
a real return-later task console. Plan first revised to filesystem task manifests, then
user selected SQLite for stronger durability. No separate Claude subagent ran in this
Codex environment.

### Model Review

Recommended first configured set:

1. Keep installed `RealESRGAN_x4plus_anime_6B.pth` for anime/illustration.
2. Keep installed `realesr-general-x4v3.pth` as fast smoke-test/fallback.
3. Add `4x_foolhardy_Remacri.pth` as the first softer/natural photo recommendation.
4. Add `RealESRGAN_x4plus.pth` as the stable official photo/general baseline.
5. Add `4x-UltraSharp.pth` only as a sharp-style option, not the photo default.

Pull and test CodeFormer/GFPGAN, HAT/DAT/OmniSR, Real-CUGAN, SPAN, and RealPLKSR as an
expanded model evaluation track. Do not expose them in the primary dropdown until
compatibility, source, license, CPU timing, memory behavior, and output preference are
verified. Face restoration models should remain a separate UI mode unless testing proves
they work cleanly as a post-process option.

Source references used for this plan:

- Real-ESRGAN official model zoo lists `RealESRGAN_x4plus` for general images,
  `realesr-general-x4v3` as a tiny lower-memory/time model, and
  `RealESRGAN_x4plus_anime_6B` as anime-optimized.
- Spandrel documents PyTorch model loading and supported SR architectures, including
  ESRGAN/Real-ESRGAN, HAT, Omni-SR, DAT, SPAN, and Real-CUGAN.
- Gradio `File` supports `file_count="multiple"` and returns a list for multi-file
  upload inputs.
- Gradio queue docs confirm event listeners are queued and default concurrency can be
  controlled with `Blocks.queue(default_concurrency_limit=...)`.
- OpenModelDB metadata identifies UltraSharp and Remacri as 4x ESRGAN `.pth` models,
  both under CC-BY-NC-SA-4.0, so they need explicit license/source documentation before
  being presented as operator-ready downloads.
