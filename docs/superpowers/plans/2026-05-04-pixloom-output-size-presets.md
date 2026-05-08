
# Pixloom Output Size Presets Plan

## Request

Add operator control for output sizing with four choices:

- 原始模型倍率
- 2K
- 4K
- 8K

## Confirmed Premise

The previous product discussion defined 2K, 4K, and 8K as target longest-side
sizes: 2048px, 4096px, and 8192px. This keeps portrait, landscape, and square
images proportional and matches Pixloom's existing `max_output_side` guard.

## Current Behavior

- The operator chooses a model.
- The model's fixed `scale` controls output size.
- Most models are 4x, Real-CUGAN is 3x, and face restoration models are 1x.
- `POST /api/batches` accepts `stored_paths`, `model_id`, `output_format`, and
  `quality`.
- SQLite task rows store model, format, quality, paths, and progress, but no
  output size intent.
- `run_upscale()` rejects outputs whose longest side would exceed
  `PIXLOOM_MAX_OUTPUT_SIDE`, currently 8192.

## Product Goal

Give non-technical operators a direct size target without exposing arbitrary
scale math. The UI should make "how big will this image become" explicit while
keeping model choice about visual style and restoration behavior.

## Proposed Contract

`output_size_preset` is a per-batch and per-task value:

```text
native -> current behavior, final size = input size * model.scale
2k     -> final longest side = 2048px
4k     -> final longest side = 4096px
8k     -> final longest side = 8192px
```

All target presets preserve aspect ratio. They are output-size goals, not model
capability claims.

## Implementation Shape

1. Add a small backend sizing module.
   - Define allowed presets and target longest sides.
   - Validate API input.
   - Compute prepared input size and final output size.
   - Preserve aspect ratio with deterministic rounding.

2. Extend SQLite task state.
   - Add `output_size_preset TEXT NOT NULL DEFAULT 'native'` to `batches`.
   - Add `output_size_preset TEXT NOT NULL DEFAULT 'native'` to `tasks`.
   - Backfill old rows through existing migration-style `_ensure_task_column`
     pattern.

3. Extend API contracts.
   - Add `output_size_preset` to `BatchCreateRequest`.
   - Include it in queued task rows and `/api/tasks` responses.
   - Return a structured batch error for invalid presets.

4. Extend worker and inference.
   - Worker passes `task.output_size_preset` into `run_upscale()`.
   - `run_upscale()` keeps native mode unchanged.
   - Target modes prepare a temporary resized input when needed, run the selected
     backend, then final-resize the backend result to the requested longest side.
   - Temporary prepared files are deleted after success or failure.
   - Output filenames include the preset, e.g. `_4x_2k.png`, while native can keep
     current `_4x.png` naming.

5. Extend frontend submission flow.
   - Add a segmented size control in `OutputParams`.
   - Send `output_size_preset` through `BatchCreateRequest`.
   - Show the chosen preset in task detail so historical tasks remain explainable.

6. Update docs and tests.
   - README, architecture, task plan, and specs mention target size presets.
   - Python tests cover preset validation, SQLite persistence, API serialization,
     native behavior, target behavior, and oversize rejection.
   - Frontend lint/build verifies the new UI contract.

## Explicit Non-Goals

- No arbitrary numeric scale input.
- No crop-to-exact 16:9 video frame behavior.
- No model chaining.
- No parallel processing.
- No GPU/CUDA path.
- No change to max input side or max output side defaults.

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|----------|
| 1 | Intake | Treat 2K/4K/8K as target longest side | Mechanical | Explicit over clever | This matches the prior answer, preserves aspect ratio, and aligns with existing max-side validation. | Fixed 16:9 canvas sizes |
| 2 | Intake | Store preset on batch and task rows | Mechanical | Completeness | Historical queue rows need to explain what was requested after refresh/restart. | UI-only transient state |

