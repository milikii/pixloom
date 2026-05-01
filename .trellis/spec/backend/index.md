# Backend Development Guidelines

> Backend conventions for the current Pixloom codebase.

---

## Overview

Pixloom backend code is a compact Python service under `app/`. There is no ORM,
no REST API layer, and no separate external worker service. The main concerns are:

- config loading
- model metadata
- file validation and persistence
- SQLite task queue state
- CPU inference orchestration
- request audit logging

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Backend module layout and ownership | Filled |
| [Database Guidelines](./database-guidelines.md) | Filesystem plus SQLite task-state rules | Filled |
| [Error Handling](./error-handling.md) | `InferenceError` contract and propagation | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Required patterns, tests, review checklist | Filled |
| [Logging Guidelines](./logging-guidelines.md) | JSONL request trace rules | Filled |

---

## Pre-Development Checklist

Before touching backend code, read:

1. `directory-structure.md`
2. `database-guidelines.md`
3. `error-handling.md`
4. `logging-guidelines.md`
5. `quality-guidelines.md`

Also read `.trellis/spec/guides/code-reuse-thinking-guide.md` and
`.trellis/spec/guides/cross-layer-thinking-guide.md` when the change touches both
UI formatting and inference behavior.
