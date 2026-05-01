# Type Safety

> Type and validation patterns for the current frontend-facing code.

---

## Overview

Pixloom frontend-facing code is Python, not TypeScript. Type safety comes from:

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

Examples:

- `app/config.py`
- `app/model_registry.py`
- `app/inference.py`

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
