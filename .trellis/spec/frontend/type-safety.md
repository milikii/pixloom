# Type Safety

> Type and validation patterns for the current frontend-facing code.

---

## Overview

Pixloom frontend-facing code is TypeScript in `frontend/` plus typed Python
contracts behind FastAPI. Type safety comes from:

- TypeScript interfaces in `frontend/src/lib/types.ts`
- dataclasses
- type annotations
- `Protocol`
- runtime validation at the backend boundary

---

## Current Contracts

- `AppConfig` defines runtime config shape
- `ResolvedModel` defines UI-visible model metadata
- `UpscaleResult` defines the success payload returned to the UI
- `InferenceError` defines the structured failure payload rendered to operators
- `frontend/src/lib/types.ts` mirrors FastAPI response schemas used by the SPA

Examples:

- `frontend/src/lib/types.ts`
- `app/config.py`
- `app/model_registry.py`
- `app/inference.py`
- `app/tasks.py`
- `backend/pixloom_api/routers/`

Current examples:

- `app/config.py`: `AppConfig` owns typed runtime paths, size limits, history
  limits, retention days, and database path.
- `app/model_registry.py`: `ModelSpec` and `ResolvedModel` define registry and
  UI-visible model metadata, including Chinese guidance fields and dropdown group
  metadata such as `group`, `group_label_zh`, `group_order`, `sort_order`, and
  `priority_stars`.
- `app/inference.py`: `UpscaleRequest`, `UpscaleResult`, and `InferenceError`
  define the request, success, and expected-failure contracts.
- `app/tasks.py`: `BatchRecord`, `TaskRecord`, and `TaskDeleteResult` define the
  SQLite queue payloads that the UI can display or delete.
- `tests/test_config.py`, `tests/test_model_registry.py`,
  `tests/test_inference_validation.py`, and `tests/test_tasks.py`: validate these
  typed contracts at their module boundaries.

---

## Validation Rules

- Validate uploads before inference starts.
- Validate output format before saving files.
- Validate model availability before expensive backend work.
- Prefer explicit coercion (`int(quality)`) at the UI boundary instead of trusting
  raw component values.

---

## Forbidden Patterns

- untyped `dict` payloads passed across module boundaries when a dataclass exists
- raw `Any` for app-owned contracts
- relying on UI labels as validation instead of checking again in Python
