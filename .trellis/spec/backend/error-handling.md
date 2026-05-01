# Error Handling

> How backend errors are modeled, propagated, and exposed in Pixloom.

---

## Overview

Pixloom uses a small explicit error contract. Backend code should raise
`InferenceError` with structured fields instead of raw strings.

The current contract lives in `app/inference.py` and is rendered for operators in
`app/app.py`.

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

---

## Propagation Pattern

- Validate early in `app/inference.py`.
- Raise `InferenceError` with a stable code and Chinese operator-facing text.
- Let `app/app.py` format the final status text with request id included.
- Wrap unexpected backend exceptions into `InferenceError` before returning to the
  UI boundary.

Do not leak tracebacks or raw internal exception messages directly to the user.

---

## Current Boundary Contract

Backend layer:

- raises `InferenceError`
- logs the failure with `request_id`
- cleans up partial files

UI layer:

- converts `InferenceError` to a readable Chinese multiline status block
- logs UI-side rejections such as missing image or unavailable model

Relevant files:

- `app/inference.py`
- `app/app.py`

Current examples:

- `app/inference.py`: `_validate_image_file`, `_validate_output_size`,
  `_ensure_backend_supported`, and `run_upscale` raise or wrap `InferenceError`
  with stable codes and Chinese next steps.
- `app/app.py`: `format_error_message`, `_ui_error`, `handle_upscale`, and
  `handle_batch_upscale` render failures with request ids instead of raw
  exception strings.
- `tests/test_inference_validation.py` and `tests/test_app_handler.py`: cover
  validation failures, backend failures, missing-model UI rejection, and request
  id propagation.

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
