<!-- /autoplan restore point: /root/.gstack/projects/milikii-pixloom/pixloom-v1-implementation-autoplan-restore-20260501-114500.md -->
# Pixloom V1.1 Model Polish And Phone Acceptance Closure Plan

## Goal

Close the remaining V1.1 gap by turning Pixloom's model story into a trusted local
operator contract. The app already has durable SQLite task state, multi-image
sequential processing, Chinese-first task UI, request-id error handling, JSONL
audit logs, safe task deletion, and retention cleanup. The remaining work is to
build a locally validated model matrix, download and evaluate the broader
high-quality model pool the user wants, and then decide which subset should be
exposed as operator-facing defaults.

## Current State

- Queue, batch upload, task list, deletion, and retention behavior are already
  implemented in code and documented in `README.md`, `docs/ARCHITECTURE.md`, and
  `docs/PROGRESS.md`.
- The current Gradio UI already shows Chinese-first model guidance and the refined
  recommendation ordering from `app/model_registry.py`.
- `docs/MODEL_EVALUATION.md` already defines the intended five-slot operator set:
  natural photo, stable photo baseline, sharp illustration, anime baseline, and
  fast smoke test.
- The user explicitly wants the broader high-quality model pool downloaded and
  evaluated locally, and local memory is not considered a limiting factor for this
  planning pass.
- `docs/PROGRESS.md` still lists unresolved manual checks for phone browser
  rendering, request-id failure correlation, real batch persistence, and safe
  delete behavior.
- `docs/TASKS.md` still shows part of `Model configuration polish` unchecked even
  though the implementation and docs have moved forward.

## Problem To Solve

The engineering is mostly done, but the remaining product risk is no longer just
operational clarity:

1. The plan/backlog documents are slightly behind the real code, which makes future
   review noisy.
2. The model strategy is still under-validated: several recommended models are
   planned but not locally accepted on the real NAS target.
3. The project needs one closure pass that converts "implemented plus partially
   evaluated" into "locally validated model matrix, explicit launch set decision,
   and documented operator guidance."

## Premises To Confirm

1. V1.1 scope should remain closed around the current Gradio product shape; do not
   reopen queue architecture, but do allow blast-radius UI/doc/model-metadata fixes
   found during acceptance.
2. The remaining work is not only documentation truthfulness; it is also local model
   acceptance and launch-set selection.
3. The user wants the broader high-quality model pool downloaded and evaluated
   locally. Download breadth is therefore in scope.
4. Download breadth does not automatically mean operator exposure breadth. The main
   dropdown should still be limited to models that are locally accepted and clearly
   labeled.
5. Phone-browser acceptance is part of release readiness, but it is not the only
   release gate; operator model confidence is equally important.

## Proposed Product Shape

### Release Closure Flow

```text
current V1.1 code
  -> align plan/backlog docs with shipped behavior
  -> download and inventory the broader requested model pool
  -> evaluate representative models on the real NAS target
  -> choose a trusted operator launch set from the validated matrix
  -> run manual phone/NAS acceptance checks for that launch set
  -> record evidence in docs/PROGRESS.md and docs/MODEL_EVALUATION.md
  -> decide: freeze V1.1 launch set or continue broader evaluation
```

### Operator-Facing Outcome

- The model dropdown order and labels remain:
  - only for models that are locally accepted
  - with a target shape of `照片自然` / `照片通用` / `锐化插画` / `动漫插画` / `快速试跑`
  - but allowed to shrink to a smaller accepted-only set if evaluation shows that is
    the more trustworthy launch surface
- The UI guidance copy stays Chinese-first and explains fit, style, speed, status,
  and warning before submit.
- The README and task docs stop implying unfinished work that is already shipped.
- Manual acceptance evidence shows that the phone operator can:
  - understand model choice on a narrow screen
  - see request ids on failures and match them to `logs/`
  - submit a real multi-image batch and observe shared `batch_id` state
  - delete one completed task and verify only linked runtime files are removed

## Scope

### In Scope

- Backlog and plan cleanup so `docs/TASKS.md` reflects what is already shipped.
- Download/inventory review for the broader requested local model pool.
- Final operator-model positioning review using the current `docs/MODEL_EVALUATION.md`
  and `app/model_registry.py`.
- Launch-set decision work:
  - accepted-only small set vs fuller five-slot set
  - expose only trusted models in the primary dropdown
- Manual acceptance recording for:
  - phone viewport guidance readability
  - controlled failure with request-id/log correlation
  - real batch submission with persisted SQLite rows
  - completed-task deletion safety
- Progress and evidence updates in project docs after manual verification.

### Not In Scope

- New inference backends
- New task queue architecture
- Automatic model downloader
- Public auth or deployment topology changes
- Face restoration mode
- Promoting every downloaded model into the main dropdown without measured acceptance

## Engineering Approach

### 1. Document Truth Pass

Update `docs/TASKS.md` so it reflects the current implementation:

- mark already-shipped model guidance improvements as complete where appropriate
- leave only truly unverified or future model evaluation work unchecked
- avoid reopening queue/batch items that are already finished and tested

Update `docs/PROGRESS.md` to distinguish:

- implemented and verified
- downloaded and under local evaluation
- implemented but still awaiting manual acceptance evidence
- future roadmap items

### 2. Model Strategy Closure

Treat `docs/MODEL_EVALUATION.md` as the single source of truth for the operator set.
This plan should confirm that `app/model_registry.py`, README operator guidance, and
model evaluation docs all say the same thing for accepted models, while also
expanding the local evaluation pool the user requested:

- `4x Remacri` is the natural-photo default candidate once locally accepted
- `RealESRGAN_x4plus` is the stable photo baseline
- `4x UltraSharp` is a sharp-style option, not the portrait default
- `RealESRGAN_x4plus_anime_6B` is the anime baseline
- `realesr-general-x4v3` is the fast smoke-test choice
- `CodeFormer`, `GFPGAN`, `HAT`, `DAT`, `OmniSR`, `Real-CUGAN`, `SPAN`, and
  `RealPLKSR` should be tracked as downloaded evaluation candidates if the user
  provides the files or sources

If wording drifts, fix the docs and registry metadata together. Downloading more
models is in scope; exposing them to ordinary operators is still gated by local
acceptance.

### 3. Local Model Matrix Closure

Produce a real NAS-side matrix for representative candidates:

- source / license clarity
- checksum or equivalent file identity record
- file presence and filename contract
- backend compatibility
- evaluation bucket: inventory-only / runtime-evaluable / operator-visible candidate
- elapsed time
- memory behavior if observed
- output judgment on representative images
- operator recommendation state: accepted, hold, or experimental

The output of this step is a launch decision, not just a note collection.

### 4. Manual Acceptance Closure

Record one focused V1.1 acceptance pass on real hardware:

- phone browser opens the current UI and model guidance reads clearly
- one forced failure surfaces Chinese guidance and a visible request id
- the matching JSONL log lines can be found under `logs/`
- one real batch creates one `batch_id` with multiple task rows in SQLite
- deleting one completed task removes only its linked input/output paths

The outcome should be written into `docs/PROGRESS.md`. If model-specific timing or
quality is learned during this pass, also append it to `docs/MODEL_EVALUATION.md`.

## Tasks

1. Clean up planning/docs drift.
   - Reconcile `docs/TASKS.md` with shipped V1.1 behavior.
   - Make sure `docs/PROGRESS.md` names model-polish/manual-acceptance as the true
     remaining work.

2. Download and inventory the requested broader model pool.
   - Record which requested models are present locally, still missing, blocked by
     backend, or blocked by license/source uncertainty.
   - Keep download breadth and operator exposure breadth explicitly separate.

3. Reconfirm the operator launch-set story.
   - Compare `app/model_registry.py`, `README.md`, and `docs/MODEL_EVALUATION.md`.
   - Decide between a smaller accepted-only set and a fuller five-slot set.
   - Define the contract between downloaded evaluation models and operator-visible
     models.
   - Define a publish rule for underfilled launch sets.
   - Fix wording drift if any file implies a different recommendation order or
     operator category.

4. Run and record manual acceptance.
   - Real phone viewport readability check.
   - Controlled failure with request id and JSONL correlation.
   - Real multi-image batch with one `batch_id`.
   - Real partial batch with at least one failed item and one successful item.
   - At least one downloaded-but-unapproved model present locally while confirming it
     does not leak into the primary submission flow.
   - One completed-task delete safety check.

5. Close V1.1 status.
   - Update `docs/PROGRESS.md` with evidence and any remaining caveats.
   - Record the explicit post-review decision: freeze launch set, continue model
     evaluation, or reopen a new adoption bottleneck.
   - Leave next-step roadmap items clearly separated as post-V1.1 work.

## Tests And Verification

This plan should not stay documentation-only if local evaluation reveals runtime
contract drift. Expected verification mix:

- `.venv/bin/pytest -q` as regression confirmation after any doc-adjacent code tweak
- targeted registry and handler tests if acceptance/exposure semantics change
- targeted batch-ingest tests if failure-safe intake behavior changes
- explicit validation that a downloaded-but-unapproved model does not appear in the
  primary dropdown when accepted-only rules apply
- manual phone-browser verification
- manual inspection of `logs/` and `state/pixloom.sqlite3`
- runtime file inspection under `input/` and `output/`

## Deliverables

- Narrow closure plan for `autoplan`
- Local model evaluation matrix with acceptance states
- Explicit launch-set decision
- Updated `docs/TASKS.md` that matches reality
- Updated `docs/PROGRESS.md` with final manual-acceptance evidence
- Optional `docs/MODEL_EVALUATION.md` additions if real acceptance produces new
  timing/quality data

## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|----------------|-----------|-----------|----------|
| 1 | Intake | Create a new closure plan instead of reusing the queue/batch plan | Mechanical | Explicit over clever | The old plan mostly covers shipped engineering work; rerunning review on it would create noise. | Reopening the broad queue/batch scope |
| 2 | Scope | Keep this plan focused on model polish and manual acceptance | Mechanical | Bias toward action | The remaining risk is operational clarity, not missing architecture. | Mixing in new backends or downloader work |
| 3 | Product | Treat phone-browser acceptance as release readiness, not optional polish | Mechanical | Choose completeness | The real operator uses a phone, so readability and failure recovery must be verified on that surface. | Declaring V1.1 done from desktop-only testing |
| 4 | CEO | Keep V1.1 boundary closed, but explicitly allow tiny blast-radius copy or doc fixes discovered during acceptance | Mechanical | Pragmatic | Manual acceptance is allowed to surface contained wording or documentation fixes without reopening architecture scope. | Pretending acceptance can never imply any code/doc touch-up |
| 5 | CEO | Require a post-closure decision output, not just cleaner docs | Mechanical | Bias toward action | Closure must end in a real product decision such as freeze V1.1, shrink launch set, or queue the next adoption bottleneck. | Treating evidence collection as the final outcome |
| 6 | User override | Expand local model download/evaluation scope because the user explicitly wants the broader high-quality pool and local memory is not the bottleneck | User Challenge | User decision | Broader local evaluation is now in scope, but operator exposure remains gated by acceptance. | Keeping download scope narrowly limited to the five current recommended slots |
| 7 | Design | Keep downloaded-but-unapproved models out of the primary mobile submission flow | Mechanical | Explicit over clever | The current UI already has a clean primary path; mixing research inventory into it would overload operators. | Showing every downloaded model in the main dropdown |
| 8 | Design | Treat partial batch as a first-class user-visible state | Mechanical | Choose completeness | Batch summary text alone is not strong enough on phone screens; partial success must be called out explicitly. | Leaving partial success implied by preview + logs only |
| 9 | Eng | Treat `app/model_registry.py` as the runtime operator surface and `docs/MODEL_EVALUATION.md` as the evidence ledger | Mechanical | DRY | One runtime filter must drive the UI; docs alone cannot be the execution truth. | Trying to mirror every downloaded file into the runtime dropdown contract |
| 10 | Eng | Add targeted tests if exposure semantics or batch-ingest failure safety changes | Mechanical | Choose completeness | These are the highest-risk regressions for this plan and should not be left to manual checks alone. | Relying on phone-side manual acceptance as the only verification |

## GSTACK REVIEW REPORT

### Phase 1: CEO Review

#### Step 0A: Premise Challenge

This plan is pointed at the right remaining problem, but one premise needs to be made
explicitly narrower: the goal is not "make model selection clearer" in the abstract,
it is "turn current model guidance plus manual verification into a shippable operator
contract." If that distinction stays fuzzy, the plan can sprawl back into model
research, downloader debates, or backend expansion that V1.1 does not need.

The strongest premise is that V1.1 should stay closed around the current Gradio
product shape. That matches the codebase, recent commits, and `docs/PROGRESS.md`.
The weakest premise is that this is "documentation truthfulness plus manual
acceptance, not a new implementation slice." That is mostly right, but it should
leave room for small code changes if manual phone acceptance finds real UX wording
drift in `app/model_registry.py` or `app/app.py`. The plan should say that such fixes
are allowed if they are contained to the blast radius.

#### Step 0B: What Already Exists

| Sub-problem | Existing code or doc to reuse |
|---|---|
| Chinese-first model guidance | `app/app.py::format_model_guidance`, `app/model_registry.py` |
| Model recommendation ordering | `app/model_registry.py`, `README.md`, `docs/MODEL_EVALUATION.md` |
| Request-id error visibility | `app/app.py::format_error_message`, `app/inference.py::InferenceError`, `app/request_logging.py` |
| Queue, batch, and SQLite task durability | `app/tasks.py`, `app/app.py`, `docs/ARCHITECTURE.md` |
| Safe delete and retention behavior | `app/tasks.py::delete_task`, `app/history.py`, `tests/test_tasks.py`, `tests/test_history.py` |
| Current release-truth docs | `README.md`, `docs/PROGRESS.md`, `docs/TASKS.md`, `docs/MODEL_EVALUATION.md` |

#### Step 0C: Dream State

```text
CURRENT
  working V1.1 code
    -> docs partly lag shipped state
    -> model strategy documented but not fully closed by manual evidence
    -> phone/operator acceptance still partly implicit

THIS PLAN
  reconcile docs with shipped behavior
    -> verify operator model story across registry + README + evaluation doc
    -> record final phone/NAS acceptance evidence
    -> declare V1.1 model-polish slice closed

12-MONTH IDEAL
  measured model matrix
    -> explicit acceptance state per model
    -> optional broader backend track
    -> operator-safe defaults grounded in real timing and quality evidence
```

#### Step 0C-bis: Alternatives Considered

| Approach | Effort | Risk | Pros | Cons |
|---|---:|---:|---|---|
| A. Closure pass only | S | Low | Finishes V1.1 cleanly, aligns docs with reality, protects focus | Does not advance broader model exploration |
| B. Closure + broader model evaluation | M | Medium | Captures more long-term model knowledge in one pass | Reopens scope, delays release closure, mixes product and R&D |
| C. Declare V1.1 done with no extra pass | XS | High | Fastest administrative closeout | Leaves operator-readiness claims under-verified and docs partially stale |

Recommendation: A. It covers the real release gap without dragging future model
research into the current release boundary.

#### Step 0D: Mode Analysis

`SELECTIVE EXPANSION` is still the right CEO mode for this plan. The base scope is
correct: close the existing release. The only expansions worth considering are those
inside the blast radius, such as recording one model timing matrix row during the
manual acceptance run or allowing a tiny UI copy correction if the phone check shows
confusing wording. Anything larger belongs in post-V1.1 planning.

#### Step 0E: Temporal Interrogation

- Hour 1: align plan/docs and define the exact acceptance checklist.
- Hour 6: run real phone/NAS checks, capture request-id/log evidence, confirm one
  real batch and one delete flow.
- Next week: either V1.1 is credibly closed, or the team discovers one or two
  contained UX/doc mismatches and fixes them quickly.
- Six months: the regret scenario is not "we didn't add more models." The regret
  scenario is "we declared readiness without a real operator acceptance record, so
  nobody trusts the docs or the recommended defaults."

#### Step 0F: CEO Mode Confirmation

Keep the plan in closure mode. Do not silently expand it into a new backend or model
research initiative. Allow only blast-radius expansions that directly strengthen the
credibility of the V1.1 release claim.

#### Error & Rescue Registry

| Failure | Why it matters | Rescue path in this plan |
|---|---|---|
| Phone UI guidance is unreadable on narrow screens | The real operator mis-picks models and loses trust | Record the failure, tighten wording or layout copy in blast radius, rerun phone check |
| Failure request id does not map cleanly to logs | Support/debug flow is weaker than docs claim | Trigger controlled failure, verify JSONL correlation, fix doc or UI wording if mismatched |
| Real batch does not persist one `batch_id` with multiple tasks | Core "submit now, return later" claim is overstated | Inspect `state/pixloom.sqlite3`, record evidence, treat mismatch as release blocker |
| Delete flow removes the wrong files or leaves ambiguity | Dangerous operator action with trust impact | Verify linked-file-only deletion on real runtime files, keep logs append-only |

#### Failure Modes Registry

| Failure mode | Severity | Current status | Required closure |
|---|---|---|---|
| Docs imply unfinished work that is already shipped | Medium | Present in `docs/TASKS.md` | Align backlog and release docs |
| Release declared done without phone evidence | High | Not yet closed | Record manual phone acceptance evidence |
| Recommended model categories drift across files | Medium | Possible | Compare registry, README, and evaluation doc in one pass |
| Manual checks remain vague and never become evidence | High | Present in `docs/PROGRESS.md` | Convert checklist items into dated verification notes |

#### NOT in Scope

- New model backends
- Automatic model download flow
- Parallel inference or queue redesign
- Face restoration mode
- Expanding the primary operator dropdown with experimental or unaccepted models

#### Dream State Delta

After this plan, Pixloom should not merely "have the right code." It should have a
credible, evidence-backed story for what the operator sees, which model to choose,
how failures are traced, and why V1.1 is considered closed. The delta from the
12-month ideal is broader model readiness and deeper timing data, not basic operator
confidence.

#### Completion Summary

| Review Area | Verdict | Notes |
|---|---|---|
| Problem framing | Strong | Right remaining problem: release closure, not new feature work |
| Scope control | Strong with one caveat | Must explicitly allow tiny blast-radius fixes if phone acceptance finds wording drift |
| Alternatives | Adequate | Closure-only path is clearly best for this release boundary |
| Risk coverage | Moderate | Manual acceptance steps are right but need to be treated as release-gating evidence |
| Strategic regret risk | Medium | Main risk is claiming readiness without evidence, not missing more models |

#### CODEX SAYS (CEO — strategy challenge)

Codex's strongest challenge is that this plan currently reads like an internal
closure exercise, not a product decision engine. It argues that "doc alignment +
manual acceptance" has not been proven to be the highest-value remaining problem, and
that the plan still assumes rather than proves three things: the operator is mainly a
phone user, a five-slot model taxonomy is the right UI abstraction, and closure
should preserve that full taxonomy instead of allowing a smaller accepted-only launch
set.

Codex also pushed on the missing business decision at the end of the work. A closure
plan that ends only in cleaner docs can succeed administratively while still failing
to move the product forward. The fix it recommends is to make the output of this plan
an explicit decision point: freeze V1.1, ship a smaller trusted model set, or reopen
the next real adoption bottleneck.

#### CLAUDE SUBAGENT (CEO — strategic independence)

The independent subagent agreed on the same core concern from a different angle:
the unclosed risk is not document drift, it is that the recommended model set is not
yet locally accepted on real hardware. In that framing, `docs/MODEL_EVALUATION.md`
and the registry status fields matter more than backlog neatness. It also flagged a
missing alternative: launch with a smaller but trusted accepted-only set rather than
insisting on a fully narrated five-slot story before the evidence exists.

A second subagent theme is that the current acceptance checklist over-indexes on
mechanism correctness that already has automated test coverage. The plan should shift
manual effort toward model-outcome validation: representative image, chosen model,
elapsed time, and quality judgment, with queue/delete/log behavior treated as smoke
checks rather than the primary definition of success.

#### CEO DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                               Subagent  Codex  Consensus
  ──────────────────────────────────────── ───────── ────── ─────────
  1. Premises valid?                       partial   partial DISAGREE WITH PLAN
  2. Right problem to solve?               no        no      CONFIRMED
  3. Scope calibration correct?            mixed     mixed   CONFIRMED
  4. Alternatives sufficiently explored?   no        no      CONFIRMED
  5. Competitive/adoption risks covered?   no        no      CONFIRMED
  6. 6-month trajectory sound?             risky     risky   CONFIRMED
═══════════════════════════════════════════════════════════════
```

Interpretation:

- Both voices agree the current plan underestimates the product risk and frames the
  remaining work too internally.
- Both voices agree a smaller accepted-only launch set must be considered as a real
  alternative.
- Neither voice recommended reopening queue or backend architecture by default; they
  recommended reframing the closure target around trusted operator outcomes.

#### CEO User Challenge

Both outside voices challenge the current direction in one important way:

- The plan should not be centered on "doc cleanup + phone acceptance closure."
- The plan should be centered on "produce a trusted, locally accepted operator model
  matrix and then decide what the real V1.1 launch set is."

That changes the product framing, the acceptance criteria, and possibly whether V1.1
ships with the full five-slot story or a smaller accepted-only set.

### Phase 2: Design Review

#### Step 0: Design Scope Assessment

Initial design completeness rating: 6/10.

This is not a greenfield visual design problem. The current Gradio UI already exists,
and the plan is not inventing a new screen system. The design risk is narrower:
how a larger local model pool and a possibly smaller trusted launch set are explained
without overloading the two-column mobile-first surface in `app/app.py`.

A 10/10 version of this plan would explicitly say:

- what the operator sees first when many models are installed but only some are
  operator-approved
- how accepted, experimental, and unavailable models are visually separated
- what happens on narrow mobile viewports when guidance text gets longer
- how acceptance evidence changes UI labeling without turning the dropdown into a
  research catalog

#### What Already Exists (Design)

- Existing two-column Gradio layout with upload/model controls on the left and
  preview/task surfaces on the right: `app/app.py`
- Existing Chinese-first model guidance block: `app/app.py::format_model_guidance`
- Existing model metadata fields for speed/style/stability/warning:
  `app/model_registry.py`
- Existing task, log, and status panels already competing for vertical space on the
  operator screen: `app/app.py`

#### Design Litmus Scorecard

| Dimension | Initial | Target | Notes |
|---|---:|---:|---|
| Information Architecture | 6 | 9 | Needs explicit separation of accepted vs evaluation-only models |
| Interaction States | 6 | 9 | Needs accepted / experimental / missing / unavailable state treatment |
| User Journey | 6 | 8 | Must define how an operator chooses confidently with more local models available |
| AI Slop Risk | 9 | 9 | Low risk; existing UI is functional, not generic marketing chrome |
| Design System Alignment | 8 | 9 | Must keep current Gradio language and avoid overdesign |
| Responsive & Accessibility | 5 | 8 | Need narrow-screen constraints for longer guidance text |
| Unresolved Decisions | 4 | 8 | Launch-set exposure rules are still not explicit enough |

#### Pass 1: Information Architecture

The plan currently says the local model pool can grow while the operator-facing set
may stay smaller, but it does not define where that boundary is shown in the UI.
Without that, implementation will drift toward one of two bad defaults: either every
downloaded model leaks into the primary dropdown, or the larger evaluation pool stays
totally invisible and impossible to reason about.

Add this information hierarchy:

```text
PRIMARY WORKSURFACE
  left column
    -> upload
    -> operator-approved model dropdown
    -> concise guidance for currently selected approved model
    -> output format / quality / submit

  right column
    -> result preview / download
    -> request log excerpt
    -> task list / gallery / delete actions

SECONDARY OPERATIONS CONTEXT
  docs + evaluation matrix
    -> downloaded-but-not-approved models
    -> acceptance reasons
    -> timing / quality evidence
```

Recommendation: keep the primary dropdown limited to accepted models. Put broader
evaluation inventory in docs and, if needed later, a separate advanced/operator panel,
not in the first-use submission flow.

#### Pass 2: Interaction State Coverage

The current plan covers mechanical runtime states, but it needs model-governance
states, because this plan's biggest product change is not a new screen, it is a new
classification of locally available models.

Add this state table:

```text
FEATURE                | LOADING | EMPTY | ERROR | SUCCESS | PARTIAL
-----------------------|---------|-------|-------|---------|--------
approved model list    | app start scan | no approved models yet | missing expected file / invalid metadata | accepted models visible | only 2-3 approved despite broader downloaded pool
model guidance block   | placeholder guidance | no model selected | selected model no longer available | guidance shown for approved model | evaluation note points to docs for broader pool
local evaluation docs  | n/a | no evaluation rows yet | missing evidence row / stale file names | matrix updated with acceptance state | some models downloaded but still blocked by backend/license
```

#### Pass 3: User Journey & Emotional Arc

The operator journey should no longer be framed as "pick from five nice categories."
It should be:

```text
STEP | USER DOES | USER FEELS | PLAN MUST SPECIFY
-----|-----------|------------|------------------
1 | opens app | wants one safe choice fast | accepted model list is short and trustworthy
2 | selects model | wants confidence, not taxonomy study | guidance explains fit + warning + status
3 | sees other models in docs | curious but cautious | evaluation matrix explains why some stay out of the main dropdown
4 | gets result | compares output with expectation | progress doc captures what was accepted and why
```

This is calmer than exposing a growing research catalog in the submission surface.

#### Pass 4: AI Slop Risk

No major issue. This plan is not drifting toward generic landing-page fluff. The
risk here is the opposite: an operator UI becoming too operationally dense for phone
use because model-evaluation concerns spill into the primary flow.

#### Pass 5: Design System Alignment

No DESIGN.md exists, so alignment must be against the current Gradio product
language. That means:

- keep Chinese-first explicit labels
- keep one-page utilitarian layout
- avoid introducing a second decision surface that forces operators to learn a new
  model browser just to submit one image

#### Pass 6: Responsive & Accessibility

This plan needs one explicit mobile rule: accepted-model guidance must remain scannable
within one viewport without forcing the operator to parse a research log. If more
models are downloaded than exposed, the phone screen should still show a short,
trusted list first.

Add these constraints:

- accepted-model dropdown remains the only required selection control
- guidance copy per model should fit within a compact markdown block
- downloaded-but-not-approved models are not listed in the primary mobile flow
- any later advanced list must degrade cleanly on 375px width

#### Pass 7: Unresolved Design Decisions

| Decision Needed | If Deferred, What Happens |
|---|---|
| How are downloaded-but-unapproved models surfaced? | Engineers either leak them into the dropdown or hide them entirely with no operator story |
| What exact label marks an accepted model? | `stability_zh` drifts between docs and UI |
| What is the fallback if only 2 approved models exist? | The UI still narrates a five-slot story that reality cannot support |

#### Design Completion Summary

| Review Area | Verdict |
|---|---|
| Information architecture | Better after separating accepted models from evaluation-only pool |
| Interaction states | Needs model-governance states, not just runtime states |
| Journey | Must optimize for "safe first choice", not "full catalog visibility" |
| Responsive | Phone constraints need to be explicit in the plan |

#### CODEX SAYS (Design — UX challenge)

Codex's design read reinforced one central point: the current UI already has a clear
primary workflow, and this plan should not pollute it with research inventory. It
checked the real Gradio layout and confirmed the main path is upload -> model
dropdown -> guidance -> submit, with result, logs, and tasks living as secondary
surfaces. Its strongest design concern is that the plan still speaks in broad
principles rather than a concrete UI contract for accepted models, unapproved models,
and partial-batch outcomes.

#### CLAUDE SUBAGENT (Design — independent review)

The independent design review reached the same conclusion with more emphasis on
mobile behavior: the plan must explicitly define what happens when there are zero
accepted models, only 1-2 accepted models, or a batch finishes partially. It also
flagged that the guidance block is already a fixed five-field structure in code, so
the plan should stop describing it abstractly and instead lock down the contract.

#### DESIGN DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                           Subagent  Codex  Consensus
  ──────────────────────────────────── ───────── ────── ─────────
  1. Information hierarchy right?      partial   partial CONFIRMED
  2. States sufficiently specified?    no        no      CONFIRMED
  3. User journey intentional?         mixed     mixed    CONFIRMED
  4. UI decisions specific enough?     no        no      CONFIRMED
  5. Responsive strategy explicit?     no        no      CONFIRMED
  6. Accessibility/clarity adequate?   partial   partial CONFIRMED
  7. Ambiguities resolved?             no        no      CONFIRMED
═══════════════════════════════════════════════════════════════
```

Design takeaway:

- keep the first-use flow narrow and trusted
- define model-governance states explicitly
- treat partial success as a first-class user-visible state, not just a summary line
- keep downloaded-but-unapproved models out of the primary mobile flow

### Phase 3: Engineering Review

#### Step 0: Scope Challenge

This plan now spans four workstreams:

1. docs truth pass
2. local model inventory and evaluation
3. launch-set decision
4. final manual acceptance recording

That is still below the "overbuilt architecture" threshold because it does not add a
new runtime subsystem. The main engineering smell is not file count. It is hidden
coupling: the registry metadata, README operator guidance, evaluation matrix, and
manual acceptance evidence all need to move together or the product becomes
internally contradictory again.

#### What Already Exists (Engineering)

| Sub-problem | Existing implementation |
|---|---|
| Operator-approved model metadata shape | `app/model_registry.py` |
| Guidance rendering path | `app/app.py::format_model_guidance` |
| Only installed/enabled models shown in UI | `app/model_registry.py::list_available_models` |
| Failure request-id contract | `app/inference.py`, `app/request_logging.py`, `app/app.py::format_error_message` |
| Batch/task persistence | `app/tasks.py`, `tests/test_tasks.py`, `tests/test_app_handler.py` |
| Safe delete behavior | `app/tasks.py::delete_task`, `tests/test_tasks.py`, `tests/test_history.py` |

#### Architecture ASCII Diagram

```text
downloaded model files
  -> models/
     -> model_registry definitions
        -> acceptance metadata in docs/MODEL_EVALUATION.md
        -> operator-approved subset in app/model_registry.py
           -> format_model_guidance()
              -> Gradio dropdown + guidance block

manual evaluation run
  -> representative image set
     -> run chosen model(s)
        -> observe elapsed time / output quality / failure behavior
           -> record matrix row in docs/MODEL_EVALUATION.md
              -> decide ACCEPT / HOLD / EXPERIMENTAL
                 -> sync README + docs/TASKS.md + docs/PROGRESS.md
```

#### Section 1: Architecture Review

The architecture is sound if the plan treats `docs/MODEL_EVALUATION.md` as the
evidence ledger and `app/model_registry.py` as the curated operator surface, not as
two equal copies of the same truth. The hidden trap is trying to make the registry
mirror every downloaded file. That collapses the distinction between "locally
present" and "operator-approved."

Recommendation: preserve a deliberate asymmetry.

- `docs/MODEL_EVALUATION.md`: broad inventory + evidence
- `app/model_registry.py`: narrow curated operator set
- `README.md`: the currently recommended launch set, not the whole inventory

#### Section 2: Code Quality Review

No new service layer is needed. The plan should explicitly avoid introducing a second
registry or a generated doc-sync script unless drift becomes frequent enough to justify
it. For now, the right move is explicit synchronized edits across a small number of
files.

The real code-quality risk is duplicated status language. If acceptance labels such as
`已实机跑通`, `待本机验收`, `未启用`, and any new "已接受" wording change, search-first
discipline matters. This is a cross-layer wording contract, not cosmetic text.

#### Section 3: Test Review

The current plan under-specifies test expectations for the only code-touch that may
still happen: narrowing or reclassifying the model registry and any guidance copy
changes that fall out of acceptance.

Test diagram:

```text
CODE PATHS                                            USER FLOWS
[+] app/model_registry.py                             [+] Operator model selection
  ├── get_default_registry()                            ├── [★★★ TESTED] guidance renders in Chinese
  │   ├── [★★  TESTED] installed/enabled filtering      ├── [GAP] accepted-only launch set still yields sane dropdown ordering
  │   ├── [GAP] accepted-vs-experimental classification ├── [GAP] operator sees only trusted choices when broader pool exists
  │   └── [GAP] renamed stability labels sync           └── [GAP] no-approved-model fallback after stricter acceptance rules
  └── list_available_models()                         

[+] docs / manual acceptance                           [+] Runtime smoke checks
  ├── [GAP] evaluation matrix row template             ├── [★★★ TESTED] request id visible on failure path
  ├── [GAP] launch-set decision recorded               ├── [★★★ TESTED] batch_id grouping in handler tests
  └── [GAP] freeze/continue decision output            └── [★★★ TESTED] safe delete semantics in task tests

COVERAGE: runtime mechanics are strong; operator-acceptance decision paths are weakly specified.
```

Required tests if code changes:

- `tests/test_model_registry.py`
  - accepted-only subset ordering
  - stricter acceptance labels still filter correctly
  - no-approved-model fallback if launch set shrinks
- `tests/test_app_handler.py`
  - guidance text still matches accepted model categories after any wording change

Test plan artifact still needed, even if many checks are manual, because the plan
must separate automated regression from release-gating human evidence.

#### Section 4: Performance Review

The user explicitly said memory is abundant, so RAM should not be the primary
constraint for this plan. That does not remove CPU time and operator wait time as a
product constraint. Performance review therefore shifts from "can it fit?" to
"should this model be trusted in the operator flow?"

Add this rule:

- a downloaded model can remain in the local evaluation pool even if it is slow
- a model should not enter the primary operator launch set without a recorded timing
  judgment and an explicit recommendation state

#### Failure Modes

| Failure mode | Test? | Error handling? | User visibility | Gap |
|---|---|---|---|---|
| A downloaded model exists but is not yet accepted and still leaks into dropdown | Partial | n/a | High confusion | Critical if plan does not define filtering |
| Acceptance labels drift between docs and registry | Weak | n/a | Silent trust erosion | Medium |
| Only 2 models are actually trusted but docs promise 5 categories | No | n/a | Misleading operator guidance | High |
| Manual evaluation never records a launch decision | No | n/a | Endless limbo, no closure | High |

#### Parallelization Strategy

Lane A: docs truth pass (`docs/TASKS.md` -> `docs/PROGRESS.md` -> `README.md`)

Lane B: model evaluation evidence pass (`docs/MODEL_EVALUATION.md` + local evaluation notes)

Lane C: registry/guidance blast-radius code/test updates (`app/model_registry.py` ->
`tests/test_model_registry.py` -> `tests/test_app_handler.py`) only if manual
acceptance proves wording/classification drift

Execution order:

- Launch A + B in parallel.
- Decide launch set.
- Run C only if the evidence forces a code or test update.

#### Engineering Completion Summary

| Review Area | Verdict |
|---|---|
| Scope challenge | Accepted as-is after user expansion; still within current architecture |
| Architecture | Sound if evidence ledger and operator surface stay deliberately separate |
| Code quality | Main risk is wording-contract drift, not abstraction debt |
| Test review | Runtime mechanics already strong; launch-set decision logic needs clearer test hooks if code changes |
| Performance | CPU trust, not memory, is the gating concern for operator exposure |

#### CODEX SAYS (Eng — architecture challenge)

Codex's engineering challenge converged on the same hidden cost as the design and CEO
voices: the plan still underestimates how much real implementation may be needed once
you separate downloaded inventory from operator-trusted models. It confirmed in code
that the current runtime filter is only `enabled + file exists`, which means an
accepted-only launch set is not just a doc decision if stricter runtime semantics are
required.

It also reinforced that the real matrix cannot stop at presence and vague quality
notes. If a model can be downloaded but not yet trusted, the system needs explicit
rules for whether it is loadable, visible, and recommended, or the plan will drift
back into free-form status language.

#### CLAUDE SUBAGENT (Eng — independent review)

The independent engineering review found a second structural risk: the current batch
ingest path is not obviously failure-safe if a multi-file submission breaks midway
through persistence or enqueueing. That matters because this plan currently frames the
remaining work as mostly manual closure. In reality, one Friday-night discovery here
could force a contained code-and-test slice, not just a docs update.

It also flagged the trust boundary around loading third-party model files. Expanding
the local evaluation pool increases what can be loaded into process memory, so source,
license, checksum, compatibility, and human trust must become explicit gates, not
nice-to-have notes.

#### ENG DUAL VOICES — CONSENSUS TABLE

```text
═══════════════════════════════════════════════════════════════
  Dimension                           Subagent  Codex  Consensus
  ──────────────────────────────────── ───────── ────── ─────────
  1. Architecture sound?               mixed     mixed    CONFIRMED
  2. Test coverage sufficient?         no        no       CONFIRMED
  3. Performance risks addressed?      partial   partial  CONFIRMED
  4. Security/trust boundary covered?  no        no       CONFIRMED
  5. Error paths handled?              no        no       CONFIRMED
  6. Deployment/operation risk ok?     partial   partial  CONFIRMED
═══════════════════════════════════════════════════════════════
```

Engineering takeaway:

- explicit operator-vs-evaluation contract may require a small runtime/test slice
- batch ingest failure safety is not yet strong enough to treat as purely manual closeout
- model loading trust gates need to be first-class acceptance criteria

### Phase 3.5: DX Review

Skipped. Pixloom is an operator-facing NAS app, not a developer platform. The plan
mentions docs and manual deployment, but its primary user is not an API/SDK consumer,
CLI integrator, or developer building on top of Pixloom.

### Cross-Phase Themes

- **Theme: internal closure vs trusted launch decision** — flagged in CEO and Eng.
  High-confidence signal that this plan must end in a concrete launch-set decision,
  not just cleaner docs.
- **Theme: downloaded inventory vs operator-visible set** — flagged in CEO, Design,
  and Eng. This is the central contract the plan must define.
- **Theme: manual evidence is necessary but not sufficient** — flagged in CEO and
  Eng. Some contained runtime/test changes may still be required if acceptance finds
  contract drift.
