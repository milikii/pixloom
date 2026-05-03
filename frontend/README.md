# Pixloom Frontend (v2 SPA)

React/Next.js SPA for the Pixloom NAS CPU image upscale console.

## Dev

```bash
cd frontend
npm install
npm run dev         # http://localhost:3000
```

The dev server proxies `/api/*` to the FastAPI backend. Make sure the backend
is running on `localhost:8000` before using the frontend:

```bash
cd ..  # project root
PYTHONPATH=. .venv/bin/uvicorn backend.pixloom_api.main:app --host 0.0.0.0 --port 8000
```

## Build

```bash
npm run build
```

Static output lands in `out/`.

## Stack

- Next.js 16 (Turbopack)
- Tailwind CSS v4 with design tokens in `globals.css`
- Lucide React icons
- @tanstack/react-query for API data fetching
- next-themes for light/dark mode

## Code structure

```
src/
├── app/            # Next.js App Router (layout, page)
├── components/
│   ├── shell/      # ShellHeader, PanelHead, ThemeToggle
│   ├── submission/ # UploadZone, ModelPicker, ModelGuidance, OutputParams, SubmitButton
│   ├── tasks/      # TaskPanel, TaskDetail, StatusBadge, TaskFilterBar, BatchActionBar
│   ├── results/    # ResultsTabs
│   └── logs/       # RequestLogs
├── hooks/          # useModels, useTasks, useSubmitBatch
├── i18n/           # Chinese-first UI copy (zh.ts)
├── lib/            # API client, TypeScript types
└── providers/      # ThemeProvider, QueryProvider
```
