# Quality Guidelines

> Code quality standards for Pixloom backend work.

---

## Required Patterns

- Use dataclasses and small explicit contracts for shared data shapes.
- Use `Path` objects instead of raw path strings in backend code.
- Validate at the boundary before expensive inference work starts.
- Clean up partial files on failure.
- Emit request-level logs for both success and failure paths.
- Keep operator-facing text Chinese-first in the UI-facing boundary.
- Use `ExposureLevel` (operator vs evaluation) to separate trusted models
  from downloaded-but-unapproved models; apply the check at both the UI
  dropdown boundary (`list_available_models`) and the worker boundary
  (`resolve_model`).

---

## Forbidden Patterns

- raw `print()` debugging in request paths
- generic user-visible `Error: ...` strings with no request id
- writing files outside configured runtime directories
- adding new persistence mechanisms without a task-level decision
- introducing framework abstractions that are larger than the code they replace

---

## Testing Requirements

- Unit tests must cover happy path and failure path behavior.
- Validation tests must cover unsupported format, invalid image content, size
  limits, and backend failures.
- UI handler tests must cover Chinese message formatting and request-id exposure.
- Logging tests must verify that JSONL rows are written for success and failure.

Current examples:

- `tests/test_inference_validation.py`
- `tests/test_app_handler.py`
- `tests/test_model_registry.py`

---

## Review Checklist

- Is there a stable error code for every expected failure?
- Does the UI get enough information to guide the user?
- Are logs correlated with request id?
- Are temporary files cleaned up when something goes wrong?
- Did the change accidentally split one concept across multiple helpers?
