# Hook Guidelines

> Stateful UI logic patterns in the current Gradio frontend.

---

## Overview

Pixloom does not use React hooks. Current stateful UI behavior is implemented with
small Python callbacks bound to Gradio events.

Examples:

- `on_submit`
- `on_model_change`
- `on_task_refresh`
- `on_task_select`
- `on_task_delete`

All current callbacks live in `app/app.py`.

---

## Current Pattern

- Keep callback logic shallow.
- Delegate real work to backend functions such as `run_upscale`.
- Use pure helper functions for repeated formatting.
- Pass explicit values into the callback; do not rely on hidden globals.

---

## Data Fetching

There is no async client-side fetch layer in v1. Data flow is:

Gradio input values -> Python callback -> backend function -> Gradio outputs

Do not add polling, browser-side fetch wrappers, or custom JS hooks unless a task
explicitly needs them.

## Current Examples

- `app/app.py`: `on_submit` delegates request handling to `handle_batch_upscale`
  and then refreshes task gallery, state, choices, and summary from backend
  storage.
- `app/app.py`: `on_model_change` is a pure callback that returns
  `format_model_guidance(model_id, models)`.
- `app/app.py`: `on_task_select`, `on_task_refresh`, and `on_task_delete` re-read
  task data through `get_task`, `list_tasks`, and `delete_task` instead of trusting
  stale browser state.
- `tests/test_app_handler.py`: exercises the callback-facing helpers through
  `handle_upscale`, `handle_batch_upscale`, and `format_model_guidance`.

---

## Common Mistakes

- building React-style abstractions in a Python Gradio app
- putting backend orchestration directly into the UI layout body
- duplicating formatting logic across callbacks instead of extracting a helper
