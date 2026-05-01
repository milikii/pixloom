# P0 UI Copy, Model Guidance, Error UX, And Logging

## Goal

Make the current Pixloom WebUI usable for the real target operator on a NAS phone workflow by fixing four blocking product gaps: Chinese-first UI copy, visible model suitability guidance, actionable error feedback, and request-level traceable logging.

## Requirements

- Convert the primary operator-facing Gradio UI copy to Chinese-first text.
- Surface model suitability guidance in the UI before inference starts.
- Introduce a small explicit error contract for user-visible failures.
- Include a request id in status and failure output so the user can report a failed run precisely.
- Emit append-only structured JSONL logs for upscale lifecycle events under `logs/`.
- Show recent successful outputs as thumbnail history items tied to their input and output files.
- Let the operator delete a selected history item, removing its linked local images.
- Add optional retention cleanup, disabled by default, to prevent old local images from growing forever.
- Keep the current CPU-only inference path and existing runtime behavior intact outside these UX and observability changes.

## Acceptance Criteria

- [ ] The main UI labels, helper text, and action button are Chinese-first.
- [ ] Selecting a model shows Chinese guidance about suitable image types and tradeoffs.
- [ ] Validation, missing-model, backend, and output-write failures produce distinct Chinese messages with suggested next actions.
- [ ] Every upscale attempt has a request id that appears in user-visible status or error output.
- [ ] Success and failure paths append structured JSONL events under `logs/`.
- [ ] Successful outputs appear in a thumbnail history list.
- [ ] Deleting a history item deletes the linked input and output files when both are safely under runtime storage directories.
- [ ] Optional retention cleanup is configurable and disabled by default.
- [ ] Tests cover the new UI copy, request-id propagation, error mapping, and log output.

## Definition of Done

- Targeted pytest suites pass.
- The current LAN-access deployment docs remain consistent with runtime behavior.
- The `.trellis/spec/backend/` and `.trellis/spec/frontend/` guideline files are updated to reflect the actual patterns introduced by this work.

## Technical Approach

- Extend model registry metadata with Chinese-facing guidance fields.
- Add a light request context and JSONL logger in the inference path.
- Add a filesystem-backed history view that reads successful request logs and existing output files.
- Record stored input paths in success logs so history deletion can remove both sides of a task.
- Add retention cleanup behind an explicit day-count environment variable.
- Replace generic `Error: ...` strings with structured error mapping at the Gradio boundary.
- Keep v1 pragmatic: explicit Chinese copy in Python, not a general i18n framework.

## Decision (ADR-lite)

**Context**: Real user testing proved the technical inference path works, but the product is still hard to operate because the UI is English-only, model fit is opaque, failures are vague, and logs are not traceable.

**Decision**: Treat operator clarity and observability as P0 product work. Implement explicit Chinese copy, model guidance, request-linked errors, and JSONL logs in the current Python codebase.

**Consequences**: Slightly more metadata and test surface area now, but much lower support/debug cost and a much more usable NAS tool immediately.

## Out of Scope

- Full i18n framework
- Multi-language toggle
- Rich analytics backend
- External log shipper or database-backed audit store
- Reworking the core inference backend architecture

## Technical Notes

- Primary code paths: `app/app.py`, `app/model_registry.py`, `app/inference.py`
- Primary tests: `tests/test_app_handler.py`, `tests/test_inference_validation.py`, plus any new log-focused tests
- Follow-up after implementation: update `.trellis/spec/backend/*.md` and `.trellis/spec/frontend/*.md` based on the final code, not assumptions
