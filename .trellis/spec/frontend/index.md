# Frontend Development Guidelines

> Frontend conventions for the current Pixloom React/Next.js operator UI.

---

## Overview

Pixloom frontend work means editing the React/Next.js SPA under `frontend/`. The
production Docker image statically exports the SPA and serves it from FastAPI on
the same `7860` origin as `/api/*`.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | React/FastAPI frontend ownership | Filled |
| [Component Guidelines](./component-guidelines.md) | React component and UI text rules | Filled |
| [Hook Guidelines](./hook-guidelines.md) | React Query and client state rules | Filled |
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
