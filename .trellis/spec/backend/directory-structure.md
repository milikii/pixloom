# Directory Structure

> How backend code is organized in Pixloom today.

---

## Overview

Pixloom v1 is a small Python service. There is no separate API layer, no database
package, and no service framework. The backend is the set of Python modules under
`app/` that support one Gradio entrypoint.

Write new backend code in the smallest existing module that owns the behavior.
Do not create extra layers just to look "enterprise".

---

## Directory Layout

```text
app/
├── app.py              # Gradio UI wiring and user-visible message formatting
├── config.py           # Environment-driven runtime configuration
├── history.py          # Filesystem-backed history listing, deletion, retention cleanup
├── inference.py        # Validation, persistence, orchestration, error contract
├── model_registry.py   # Installed model metadata and availability filtering
├── request_logging.py  # Request id generation and JSONL audit logging
└── spandrel_backend.py # Concrete CPU inference backend

tests/
├── test_app_handler.py
├── test_config.py
├── test_inference_validation.py
├── test_model_registry.py
├── test_output_paths.py
└── test_spandrel_backend.py
```

---

## Module Organization

- Keep UI formatting in `app/app.py`.
- Keep environment parsing in `app/config.py`.
- Keep history listing, history deletion, and retention cleanup in `app/history.py`.
- Keep request validation, file persistence, and request lifecycle orchestration in
  `app/inference.py`.
- Keep model metadata in `app/model_registry.py`.
- Keep request-level audit logging in `app/request_logging.py`.
- Keep heavy ML framework integration in a backend-specific module such as
  `app/spandrel_backend.py`.

If a new feature touches both the UI and backend orchestration, prefer adding a
small helper function to an existing module over inventing a new package.

---

## Naming Conventions

- Python files use `snake_case.py`.
- Public dataclasses use noun names: `AppConfig`, `ResolvedModel`, `UpscaleResult`.
- User-visible formatter helpers use verb phrases: `format_status`,
  `format_model_guidance`, `format_error_message`.
- Request lifecycle helpers should be explicit: `build_request_id`, `log_event`.

---

## Examples

- UI boundary and Chinese-first status formatting:
  - `app/app.py`
- Request validation and cleanup on failure:
  - `app/inference.py`
- History reconstruction and local file deletion:
  - `app/history.py`
- Model metadata with UI guidance fields:
  - `app/model_registry.py`
- JSONL request audit trail:
  - `app/request_logging.py`
