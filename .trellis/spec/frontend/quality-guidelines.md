# Quality Guidelines

> Frontend quality rules for the current Gradio UI.

---

## Required Patterns

- Chinese-first operator-facing copy
- Visible model guidance before the primary action
- Actionable failure text with request id
- Deterministic formatter helpers instead of inline repeated strings
- Tests for success status, failure formatting, and model guidance text
- Thumbnail history for successful outputs with clear delete behavior

---

## Forbidden Patterns

- English-only critical UI copy for the main operator flow
- generic `Error: ...` strings with no guidance
- burying key model-selection guidance in README only
- adding visual complexity without helping the operator make a better decision
- hiding destructive history deletion behind ambiguous button text

---

## Testing Requirements

- `tests/test_app_handler.py` must cover:
  - success status formatting
  - known failure formatting
  - unexpected runtime failure formatting
  - model guidance content
- History-related backend tests must cover listing, selection data, deletion, and
  retention cleanup.
- UI-related contract changes should not ship without test updates.

---

## Review Checklist

- Can a first-time operator understand which model to choose?
- Can they tell what happened when a run fails?
- Is the primary action still obvious on a phone-sized screen?
- Did a new UI string accidentally drift back to English for a critical path?
- Does the history section make it clear that deletion removes local files?
