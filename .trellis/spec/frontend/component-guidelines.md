# Component Guidelines

> UI composition patterns for the Pixloom frontend.

---

## Overview

Pixloom has two frontends:

- **V1 Gradio UI** (`app/app.py`): a "component" is a Gradio block or formatting helper.
- **V2 React SPA** (`frontend/`): standard React/Next.js component model with Tailwind CSS v4.

Both share the same backend contracts (model metadata, task records, request logging).

---

## V1 Gradio Component Pattern

1. intro copy
2. input controls column
3. result and task-list column
4. pure helper functions for rendering text

Keep `build_demo()` organized as:

- top-level page heading
- short operator guidance
- one row with two columns
- left side for multi-file input and action
- right side for preview, download, status, request logs, task selector, task list,
  and completed-output thumbnails

Examples: `app/app.py`

---

## V2 React Component Rules

### File Organization

- One component per file.
- Group by domain: `shell/`, `submission/`, `tasks/`, `results/`, `logs/`.
- Shared primitives (like `StatusBadge`) live in the domain directory of their
  primary consumer.

### Styling

- Use Tailwind utility classes only. No inline styles, no CSS modules.
- Reference semantic design tokens via Tailwind theme extensions:
  `text-success`, `bg-info-subtle`, `border-destructive-subtle`.
- Never use hardcoded Tailwind palette colors (`text-emerald-600`,
  `dark:text-blue-400`). Always map through the semantic token layer.
- Shadows use `shadow-card`, `shadow-card-hover`, `shadow-button`, `shadow-modal`.
- Border-radius uses token classes when exact design tokens are needed; otherwise
  default Tailwind radius utilities are acceptable.

### Color Semantics

| Token | CSS Var | Use |
|-------|---------|-----|
| `text-success` / `bg-success-subtle` | `--success` / `--success-subtle` | Completed task, verified state |
| `text-warning` / `bg-warning-subtle` | `--warning` / `--warning-subtle` | Slow model, interrupted task |
| `text-info` / `bg-info-subtle` | `--info` / `--info-subtle` | Running task, progress |
| `text-destructive` / `bg-destructive-subtle` | `--destructive` / `--destructive-subtle` | Failed task, delete action |

### Status Display

- Always use `StatusBadge` component for task status labels.
- Status must be conveyed through icon + color + text simultaneously.
- The `running` status shows a spinning `Loader2` icon from Lucide React.

### Component Contracts

- Props interfaces are defined inline in the component file (no separate `.d.ts`).
- Data shapes come from `@/lib/types.ts` which mirrors the FastAPI response schemas.
- API calls use `@tanstack/react-query` hooks defined in `@/hooks/`.
- Chinese-first copy comes from `@/i18n/zh.ts`; never hardcode UI strings.

---

## UI Text Rules (Shared)

- Use Chinese-first labels and operator guidance.
- Keep button text action-oriented and short.
- Expose model suitability before the user clicks start.
- Each model must carry Chinese-first guidance fields:
  `display_name_zh`, `recommended_for_zh`, `warning_zh`, `speed_zh`,
  `style_zh`, `stability_zh`. These feed the model dropdown and guidance
  block; never leave them empty for an operator-visible model.
- Status and error boxes should include request id when relevant.
- Task list must show status labels for queued/running/completed/failed/deleted/
  interrupted rows.

---

## Accessibility and Mobile Rules

- Labels must be explicit; do not rely on placeholders alone.
- Touch targets must be at least 44px.
- Focus ring: 2px accent color, offset 2px.
- Status is always conveyed through icon + color + text.
- `prefers-reduced-motion` disables all animations and transitions.
- Theme toggle uses `next-themes` mount guard to avoid hydration mismatch.

---

## Common Mistakes

- Using hardcoded Tailwind palette colors instead of semantic tokens.
- Leaving model ids unexplained.
- Showing raw exception text to the user.
- Adding extra UI sections without clear operator value.
- Duplicating status display logic instead of using `StatusBadge`.
