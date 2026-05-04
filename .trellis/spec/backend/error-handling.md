# Error Handling

> How backend errors are modeled, propagated, and exposed in Pixloom.

---

## Overview

Pixloom uses a small explicit error contract. Backend code should raise
`InferenceError` with structured fields instead of raw strings.

The current contract lives in `app/inference.py`, is persisted into task/log state
by the worker, and is exposed to operators through FastAPI task/log responses.

---

## Error Type

Use `InferenceError` for all expected user-facing failures. The object should carry:

- `code`
- `user_message_zh`
- `likely_cause_zh`
- `suggested_action_zh`
- `detail`
- `request_id`

Examples:

- unsupported upload format
- upload too large
- image decode failure
- output too large
- backend not implemented
- upscale failed
- output save failed
- model disabled (operator attempted to use a disabled model)
- model not operator-visible (operator attempted to use an evaluation-only model)
- model file missing (registry entry exists but file is absent)

---

## Propagation Pattern

- Validate early in `app/inference.py`.
- Raise `InferenceError` with a stable code and Chinese operator-facing text.
- Let FastAPI task/log endpoints expose stable error fields with the request id
  included.
- Wrap unexpected backend exceptions into `InferenceError` before returning to the
  UI boundary.

Do not leak tracebacks or raw internal exception messages directly to the user.

---

## Current Boundary Contract

Backend layer:

- raises `InferenceError`
- logs the failure with `request_id`
- cleans up partial files
- rejects evaluation-only models at the worker boundary via `resolve_model()`

API/UI layer:

- returns task records with `error_code`, `error_detail`, and `request_id`
- rejects missing image or unavailable model before enqueue when possible
- filters model dropdown through `/api/models`, backed by `list_available_models()`

Relevant files:

- `app/inference.py`
- `app/model_registry.py`
- `backend/worker/daemon.py`
- `backend/pixloom_api/routers/`

Current examples:

- `app/inference.py`: `_validate_image_file`, `_validate_output_size`,
  `_ensure_backend_supported`, and `run_upscale` raise or wrap `InferenceError`
  with stable codes and Chinese next steps.
- `backend/worker/daemon.py`: converts expected and unexpected task failures into
  failed task rows with stable error codes.
- `tests/test_inference_validation.py` and `tests/test_api.py`: cover validation
  failures, backend-facing contracts, model visibility, and request id propagation.

---

## Forbidden Patterns

- `raise ValueError("...")` for user-visible inference failures
- returning generic `Error: ...` strings without error code or next step
- showing traceback text in the status box
- swallowing unexpected exceptions without logging a request id

---

## Common Mistakes

- mixing validation and formatting in the same helper
- forgetting to attach or preserve `request_id`
- creating distinct English and Chinese meanings for the same failure
- leaving partial output files behind on save failure
