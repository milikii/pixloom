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


## Session 3: V2 design system CSS tokens and semantic color unification

**Date**: 2026-05-03
**Task**: Pixloom v2 前端设计系统
**Branch**: `pixloom-v1-implementation`

### Summary

Completed the CSS design token infrastructure for the v2 React SPA, created a reusable
StatusBadge component, and unified all existing components to reference semantic design
tokens instead of hardcoded Tailwind palette colors.

### Main Changes

- Added success/warning/info CSS custom properties with subtle background variants
  for both light and dark modes in `frontend/src/app/globals.css`.
- Added 4-level shadow system: `--shadow-card-rest`, `--shadow-card-hover-val`,
  `--shadow-button-glow`, `--shadow-modal-val` with separate light/dark values.
- Added border-radius token scale: `--radius-xs` (4px), `--radius-sm` (8px),
  `--radius-md` (12px), `--radius-lg` (16px), `--radius-full` (9999px).
- Mapped all new tokens to Tailwind v4 `@theme inline` extensions.
- Created `StatusBadge` capsule component with icon + color + text triple encoding
  for every task status. Running status shows animated `Loader2` spinner.
- Replaced inline `TaskStatusBadge` in TaskDetail.tsx with shared component.
- Updated TaskPanel.tsx: removed unused `statusColor`/`statusIcon` helpers, wired
  StatusBadge, switched delete button to `destructive-subtle` tokens.
- Fixed ModelGuidance.tsx: `text-amber-500` → `text-warning`, `text-emerald-500`
  → `text-success`.
- Fixed ThemeToggle.tsx: `text-amber-400` → `text-warning`, `text-indigo-400`
  → `text-accent`.
- Fixed page.tsx: error banner uses `border-destructive-subtle bg-destructive-subtle`.
- Removed unused imports from ResultsTabs.tsx, OutputParams.tsx, ModelPicker.tsx.
- Updated `.trellis/spec/frontend/directory-structure.md` and `component-guidelines.md`
  to document the v2 React SPA conventions.
- Updated `README.md` directory layout and description to reflect v2 architecture.
- Updated `docs/PROGRESS.md` with v2 phase status and verification entries.

### Testing

- [OK] `npx tsc --noEmit`: passed (zero errors)
- [OK] `npx eslint src/`: passed (zero errors, zero warnings)

### Git Commits

| Hash | Message |
|------|---------|
| `ea3f3f9` | feat: v1.1 model matrix closure + v2 API and SPA scaffold |
| `3db6899` | feat: complete CSS design tokens and unify component semantic colors |

### Status

[OK] **Completed** — CSS token infrastructure and component unification done;
     ready for next design system phase (mobile layout, ShellHeader ThemeToggle
     integration, animation details).

### Next Steps

- Integrate ThemeToggle into ShellHeader dark bar.
- Implement mobile-first responsive layout (<768px breakpoint).
- Add button press spring animation and card hover micro-lift.
- Verify light/dark mode renders correctly in browser.

