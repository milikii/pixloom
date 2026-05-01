# Frontend Development Guidelines

> Frontend conventions for the current Pixloom Gradio UI.

---

## Overview

Pixloom frontend work currently means editing the Gradio UI in `app/app.py` and the
metadata that feeds it. There is no standalone JS client in v1.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Where frontend-facing Python code lives | Filled |
| [Component Guidelines](./component-guidelines.md) | Gradio layout and text rules | Filled |
| [Hook Guidelines](./hook-guidelines.md) | Callback-based stateful logic | Filled |
| [State Management](./state-management.md) | Local state and request flow rules | Filled |
| [Quality Guidelines](./quality-guidelines.md) | UX and testing quality bar | Filled |
| [Type Safety](./type-safety.md) | Python contract and validation rules | Filled |

---

## Pre-Development Checklist

Before touching UI behavior, read:

1. `directory-structure.md`
2. `component-guidelines.md`
3. `state-management.md`
4. `quality-guidelines.md`

If the change also touches inference or logging contracts, read the backend
guides and `.trellis/spec/guides/cross-layer-thinking-guide.md`.
