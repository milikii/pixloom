# V1.1 Model Matrix And Launch Set Closure

## Goal

Close Pixloom V1.1 by turning the current model story into a trusted local operator
contract. Build a locally validated model matrix, keep downloaded evaluation models
separate from operator-visible accepted models, decide the real launch set, and
record the final manual acceptance evidence for phone/NAS usage.

## What I Already Know

- Queue, batch upload, task list, deletion, and retention behavior already exist in
  code and docs.
- The current UI is a Gradio two-column layout with a model dropdown, guidance block,
  request logs, and task list.
- `app/model_registry.py` currently exposes models at runtime based on `enabled` and
  local file presence, while `docs/MODEL_EVALUATION.md` carries richer evaluation
  status.
- The approved plan requires a larger local evaluation pool but still wants only
  trusted models in the main operator dropdown.
- `autoplan` identified two likely implementation gaps, not just documentation work:
  runtime accepted/exposure contract and possible batch-ingest failure-safety hardening.

## Assumptions (Temporary)

- This task remains within the current Gradio product shape and does not introduce a
  new backend or downloader.
- A smaller accepted-only launch set is valid if the broader model pool is not yet
  fully trusted.
- Manual acceptance may reveal small blast-radius code or test changes that should be
  fixed in this task.

## Open Questions

- Whether accepted/exposure semantics can stay as doc+metadata sync or must become a
  new structured runtime field in `app/model_registry.py`.
- Whether batch-ingest failure safety needs a contained code change now or can remain
  a documented risk pending explicit verification.

## Requirements

- Reconcile `docs/TASKS.md`, `docs/PROGRESS.md`, `README.md`, and
  `docs/MODEL_EVALUATION.md` with the approved closure plan.
- Define a clear contract between downloaded evaluation models and operator-visible
  accepted models.
- Preserve a small trusted primary dropdown in the UI; downloaded-but-unapproved
  models must not leak into the main submission flow.
- Define launch-set decision rules, including what happens if the accepted set is
  smaller than the target five-slot taxonomy.
- Add targeted automated tests if runtime exposure semantics or batch-ingest safety
  behavior changes.
- Record the test/acceptance matrix needed for final manual phone/NAS verification.

## Acceptance Criteria

- [ ] PRD-backed task context is configured for a fullstack change touching model
      metadata, UI guidance, docs, and tests.
- [ ] Relevant specs and code patterns are captured in task context files.
- [ ] Launch-set vs evaluation-pool contract is explicit in the plan/PRD.
- [ ] Likely code, doc, and test touch points are identified before implementation.
- [ ] Task is activated in Trellis and ready for implementation/check phases.

## Technical Notes

- Primary plan source:
  `docs/superpowers/plans/2026-05-01-pixloom-model-polish-and-phone-acceptance.md`
- Likely implementation surfaces:
  `app/model_registry.py`, `app/app.py`, `docs/MODEL_EVALUATION.md`,
  `docs/PROGRESS.md`, `docs/TASKS.md`, `README.md`,
  `tests/test_model_registry.py`, `tests/test_app_handler.py`, `tests/test_tasks.py`
- Cross-layer risk:
  runtime model exposure rules, UI explanation states, task-flow visibility, and doc
  truth all need to stay synchronized.
