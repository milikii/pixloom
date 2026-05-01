# Directory Structure

> How the Pixloom frontend is organized today.

---

## Overview

Pixloom v1 does **not** have a separate browser app. The frontend is a Gradio UI
declared in Python inside `app/app.py`.

Do not invent a `src/` React app, client-side router, or JS state layer unless a
future task explicitly requires it.

---

## Directory Layout

```text
app/
├── app.py              # Gradio Blocks layout, labels, UI event wiring
├── model_registry.py   # UI-facing model labels and guidance metadata
├── inference.py        # Status payloads returned to the UI
└── request_logging.py  # Request ids used by user-visible messages
```

---

## Module Organization

- UI structure and component wiring stay in `app/app.py`.
- Model-selection help text comes from `app/model_registry.py`.
- Status text and failure meaning should be derived from backend contracts, not
  duplicated ad-hoc in multiple places.

If a future UI change still fits Gradio, keep it in `app/app.py` and extract only
pure formatting helpers when the file starts to repeat itself.

---

## Naming Conventions

- UI formatting helpers use clear names such as `format_status`,
  `format_model_guidance`, and `format_error_message`.
- Nested callback handlers inside `build_demo()` should stay small and explicit:
  `on_submit`, `on_model_change`.
- Visible labels should be Chinese-first.

---

## Examples

- Layout and event wiring:
  - `app/app.py`
- Model guidance source:
  - `app/model_registry.py`
