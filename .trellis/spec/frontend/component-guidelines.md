# Component Guidelines

> UI composition patterns for the Gradio frontend.

---

## Overview

In Pixloom, a "component" is usually a Gradio block or a small formatting helper,
not a React component.

The current component pattern is:

1. intro copy
2. input controls column
3. result and task-list column
4. pure helper functions for rendering text

---

## Structure Pattern

Keep `build_demo()` organized as:

- top-level page heading
- short operator guidance
- one row with two columns
- left side for multi-file input and action
- right side for preview, download, status, request logs, task selector, task list,
  and completed-output thumbnails

Examples:

- `app/app.py`

---

## UI Text Rules

- Use Chinese-first labels and operator guidance.
- Keep button text action-oriented and short.
- Expose model suitability before the user clicks start.
- Status and error boxes should include request id when relevant.
- Task list must show status labels for queued/running/completed/failed/deleted/
  interrupted rows.
- Completed tasks may use small thumbnails, but failed and interrupted tasks must
  still be visible in text form.
- Deleting a task is a file deletion action, so button text must say it deletes
  the selected task.

---

## Accessibility And Mobile Rules

- Labels must be explicit; do not rely on placeholders alone.
- Keep the primary action obvious in one screen on a phone.
- Prefer multiline status text over hidden hover-only details.
- Do not bury failure guidance in README-only documentation.

---

## Common Mistakes

- Leaving model ids unexplained
- Showing raw exception text to the user
- Adding extra UI sections without clear operator value
- Treating Gradio helper text as optional polish instead of core usability
- Adding a task list that cannot remove the linked local files
