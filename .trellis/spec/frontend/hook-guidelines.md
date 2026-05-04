# Hook Guidelines

> Stateful UI logic patterns in the current React frontend.

---

## Overview

Pixloom uses React hooks under `frontend/src/hooks/` for API data fetching and
mutations. Server state goes through TanStack Query; durable task state remains in
SQLite behind FastAPI.

Examples:

- `useModels`
- `useTasks`
- `useRequestLog`
- `useFileUpload`
- `useSubmitBatch`

---

## Current Pattern

- Keep hook logic shallow.
- Delegate real work to FastAPI endpoints.
- Use typed request/response shapes from `frontend/src/lib/types.ts`.
- Invalidate or refetch task queries after mutations that change server state.

---

## Data Fetching

Data flow is:

React state -> API client -> FastAPI router -> SQLite/runtime module -> React Query

Keep API paths same-origin in production (`/api`). For local frontend development,
use `NEXT_PUBLIC_API_BASE=http://localhost:8000/api` when the FastAPI server runs
on port `8000`.

## Current Examples

- `frontend/src/hooks/useModels.ts`: fetches model metadata.
- `frontend/src/hooks/useTasks.ts`: fetches tasks, request logs, and deletes tasks.
- `frontend/src/hooks/useSubmitBatch.ts`: uploads files and creates task batches.

---

## Common Mistakes

- duplicating fetch logic outside `frontend/src/lib/api-client.ts`
- mutating durable task state only in browser memory
- bypassing typed API shapes in `frontend/src/lib/types.ts`
