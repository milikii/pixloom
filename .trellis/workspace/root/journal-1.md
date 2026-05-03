# Journal - root (Part 1)

> AI development session journal
> Started: 2026-04-30

---


## Session 1: Complete Pixloom V1.1 queue and model recommendations

**Date**: 2026-05-01
**Task**: Complete Pixloom V1.1 queue and model recommendations
**Branch**: `pixloom-v1-implementation`

### Summary

Added SQLite task queue, batch upload, task list, safe task deletion, docs/spec updates, container rebuild verification, and model recommendation metadata.

### Main Changes

- Added `PIXLOOM_DB_PATH`, `state/` persistence, and SQLite `batches`/`tasks`
  state management.
- Routed single-image and multi-image submissions through queued task rows with
  per-image `request_id` and grouped `batch_id`.
- Added sequential batch processing, failed-task visibility, restart interruption
  handling, and safe task deletion with `task_deleted` logging.
- Replaced the history-focused UI surface with a SQLite-backed task list plus
  completed-output thumbnails.
- Added model metadata for operator-facing style, speed, and local acceptance
  status; reordered recommendations around natural photos, photo baseline, sharp
  illustration, anime, and quick smoke tests.
- Updated README, architecture docs, task docs, progress notes, model evaluation,
  and Trellis backend/frontend specs.

### Git Commits

| Hash | Message |
|------|---------|
| `2477127` | (see git log) |
| `a16fad0` | (see git log) |

### Testing

- [OK] `.venv/bin/python -m compileall app tests`
- [OK] `.venv/bin/pytest -q` (`60 passed`)
- [OK] `docker compose build`
- [OK] `docker compose up -d --force-recreate`
- [OK] container-internal HTTP probe returned `200`

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 2: V1.1 model matrix and launch set closure

**Date**: 2026-05-03
**Task**: V1.1 model matrix and launch set closure
**Branch**: `pixloom-v1-implementation`

### Summary

Closed the V1.1 model matrix and launch set task: audited the exposure contract in code, verified batch-ingest failure safety, reconciled all docs, enhanced test coverage, and made the final closure decision to keep the 7-model operator set.

### Main Changes

- Added `exposure` check to `resolve_model()` in `app/model_registry.py` so that
  enabled-but-evaluation-only models are rejected at the worker boundary (defense-
  in-depth for the operator-visible contract).
- Audited batch-ingest failure safety: `create_batch_with_tasks` uses
  `BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK`, input cleanup on failure, and post-commit
  log-failure reversal. No code changes needed.
- Marked the final V1.1 task item as done in `docs/TASKS.md`.
- Added a `Closure Decision` section to `docs/PROGRESS.md` documenting the
  decision to keep the current 7-model operator launch set.
- Updated all doc dates to 2026-05-03 across `README.md`, `docs/TASKS.md`,
  `docs/PROGRESS.md`, `docs/MODEL_EVALUATION.md`, and
  `docs/V1_1_ACCEPTANCE_CHECKLIST.md`.
- Added `model_inventory.py` and `model_matrix.py` to README directory layout.
- Added `test_resolve_model_rejects_enabled_evaluation_model` test.
- Updated `.trellis/spec/backend/directory-structure.md` with new modules
  (`model_inventory.py`, `model_matrix.py`, `tasks.py`) and their test files.
- Ran `model_inventory` CLI (verified 7 operator + 9 evaluation models) and
  `model_matrix` smoke test (1 model passed, 23.772s on real image).

### Testing

- [OK] `python3 -m compileall app tests`
- [OK] `.venv/bin/pytest -q` (`78 passed`; +1 test for exposure edge case)

### Status

[OK] **Completed** — code and docs ready; manual phone/NAS acceptance pass remains
     per `docs/V1_1_ACCEPTANCE_CHECKLIST.md`.

### Next Steps

- Manual phone/NAS acceptance per `docs/V1_1_ACCEPTANCE_CHECKLIST.md`.
- Re-evaluate launch set after manual acceptance pass.
