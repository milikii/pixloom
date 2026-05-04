# Directory Structure

> How the Pixloom frontend is organized today.

---

## Overview

Pixloom uses a React/Next.js SPA under `frontend/` served by a FastAPI backend
under `backend/`. Production is one container and one external port: FastAPI serves
`/api/*`, `/api/files/*`, and the static frontend export on `7860`.

---

## Directory Layout

```text
frontend/
├── src/
│   ├── app/            # Next.js App Router (layout, page, globals.css)
│   ├── components/
│   │   ├── shell/      # ShellHeader, PanelHead, ThemeToggle
│   │   ├── submission/ # UploadZone, ModelPicker, ModelGuidance, OutputParams, SubmitButton
│   │   ├── tasks/      # TaskPanel, TaskDetail, StatusBadge
│   │   ├── results/    # ResultsTabs
│   │   └── logs/       # RequestLogs
│   ├── hooks/          # useModels, useTasks, useSubmitBatch
│   ├── i18n/           # Chinese-first copy (zh.ts)
│   ├── lib/            # api-client, types
│   └── providers/      # QueryProvider, ThemeProvider
├── package.json
├── next.config.ts
└── tsconfig.json
```

---

## Module Organization

- React components live under `frontend/src/components/` organized by domain
  (shell, submission, tasks, results, logs).
- Design tokens (colors, shadows, border-radius) are defined as CSS custom properties
  in `frontend/src/app/globals.css` and mapped to Tailwind v4 `@theme` extensions.
- Theme switching uses `next-themes` with `class` attribute, defaulting to `light`.
- API client code in `frontend/src/lib/api-client.ts` calls the FastAPI backend.
- Chinese-first UI copy lives in `frontend/src/i18n/zh.ts`.

---

## Naming Conventions

- React components use PascalCase filenames: `ShellHeader.tsx`, `StatusBadge.tsx`.
- Hooks use `use` prefix: `useModels.ts`, `useTasks.ts`.
- UI formatting helpers use clear names such as `formatElapsed`, `formatTime`.
- CSS custom properties use semantic names: `--success`, `--warning`, `--info`,
  `--shadow-card-rest`, `--radius-md`.
- Visible labels are Chinese-first.

---

## Examples

- V2 React SPA entry and page shell:
  - `frontend/src/app/page.tsx`
  - `frontend/src/app/layout.tsx`
- Design tokens:
  - `frontend/src/app/globals.css`
- Semantic status badge component:
  - `frontend/src/components/tasks/StatusBadge.tsx`
