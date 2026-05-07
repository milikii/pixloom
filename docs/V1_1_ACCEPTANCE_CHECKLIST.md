# Pixloom V1.1 Acceptance Checklist

Last updated: 2026-05-08

## Goal

Run one focused manual acceptance pass for the current V1.1 launch-set contract:

- the primary dropdown shows only operator-visible accepted models
- request-id failure tracing works end to end
- batch and partial-batch behavior is clear from the UI
- task deletion removes only linked runtime files

## Current Expected Operator-Visible Models

The current runtime-visible set intentionally keeps all usable local models exposed:

- `SPAN 4x`
- `RealPLKSR 4x`
- `照片修复 - 4x NMKD-Siax`
- `锐化插画 - 4x UltraSharp`
- `DRCT 4x`
- `质量上限 - HAT-L 4x`
- `DRCT-L 4x`
- `APISR 4x`
- `动漫修复 - Real-CUGAN 3x 去噪`
- `动漫精修 - Real-CUGAN 2x 去噪`
- `动漫插画 - Real-ESRGAN Anime 6B`
- `CodeFormer`
- `GFPGAN v1.4`
- `快速试跑 - Real-ESRGAN General v3`
- `照片自然 - 4x Remacri`
- `照片通用 - Real-ESRGAN 4x`

Other local model files may exist in `models/`, but they should not appear in the
primary submission dropdown unless they are explicitly promoted into the operator set.

## Before You Start

1. Rebuild and restart the app:

```bash
docker compose build
docker compose up -d --force-recreate
```

2. Confirm the app is reachable:

```bash
docker compose logs --tail=80 pixloom
```

3. Confirm current local model inventory:

```bash
find models -maxdepth 1 -type f | sort
python3 -m app.model_inventory
```

4. Confirm current task database path:

```bash
ls -lh state/pixloom.sqlite3
```

## Acceptance Run

### 1. Phone UI Load

Open the app from a real phone browser.

Expected:

- page loads
- the main action is visible without hunting
- the dropdown only shows the current accepted operator models
- output size choices show `原始`, `2K`, `4K`, and `8K` before hidden save parameters
- the right side is split into `结果` / `任务` / `日志` tabs instead of one long panel
- if more local model files exist than the dropdown shows, the guidance/status copy
  explains that only accepted models are currently exposed

Record:

- phone model / browser
- whether the model guidance is readable on first viewport
- whether the task/log tabs feel shorter and easier to scan than the old long sidebar
- whether the accepted-only behavior is obvious

### 2. Controlled Failure With Request ID

Use one controlled failure path and capture the request id shown in the UI.

Recommended low-risk method:

1. Open the app and select an accepted model in the dropdown.
2. Select `CodeFormer` or `GFPGAN v1.4`.
3. Submit a normal non-face image.
4. Confirm the task fails with a Chinese `NO_FACE_DETECTED` style error and a
   request id.

Pre-queue validation failures, such as selecting a model whose file is missing, now
return a structured 4xx API error and log `ui_rejected`; they are useful API-boundary
checks, but they are not task lifecycle checks because no task row is created.

Evidence to collect:

- error code shown in UI
- request id shown in UI
- matching JSONL lines:

```bash
grep -R "<REQUEST_ID>" logs
```

### 3. Real Batch

Submit one real batch from a phone with at least 2 images.

Run at least one image with `原始` and one with `2K` or `4K`.

Expected:

- one `batch_id`
- multiple `request_id`s
- task list shows all items
- completed items remain visible after refresh

Evidence:

```bash
sqlite3 state/pixloom.sqlite3 "select batch_id, request_id, status, input_filename, output_size_preset from tasks order by created_at desc limit 10;"
```

### 4. Real Partial Batch

Submit one batch where at least one item succeeds and one item fails.

Expected:

- status text clearly says this is partial success, not full success
- failed item is visible in task text/list
- the user knows to inspect the task list for details

Evidence:

- screenshot or notes of the returned status text
- matching task rows:

```bash
sqlite3 state/pixloom.sqlite3 "select batch_id, request_id, status, error_code from tasks order by created_at desc limit 10;"
```

### 5. Delete Safety

Delete one completed task from the WebUI.

Expected:

- only linked input/output files are removed
- task row becomes `deleted`
- audit log keeps the delete event

Evidence:

```bash
sqlite3 state/pixloom.sqlite3 "select request_id, status, input_path, output_path from tasks order by created_at desc limit 10;"
grep -R "task_deleted" logs
```

## Local Model Matrix Capture

For every model you actually place in `models/`, record:

- file name
- checksum / file identity
- backend compatibility
- elapsed time
- output judgment
- operator recommendation state

Suggested commands:

```bash
find models -maxdepth 1 -type f | sort
sha256sum models/*
ls -lh models
python3 -m app.model_inventory
.venv/bin/python -m app.model_matrix --input input/1777260396442.png
```

Write the results back into `docs/MODEL_EVALUATION.md`.

## Closure Decision

After the acceptance run, make one explicit decision:

- keep the current small accepted launch set
- expand the accepted launch set
- continue evaluation before expanding

Record that decision in `docs/PROGRESS.md`.
