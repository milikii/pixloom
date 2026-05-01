# Skill Integration Guide

> **Purpose**: Adapt reusable skills into project development guidelines without
> accidentally turning a workflow import into product code.

---

## Core Rule

Skill integration updates project conventions, not runtime behavior.

When integrating a skill:
- Put project rules in `.trellis/spec/{target}/` or `.trellis/spec/guides/`.
- Put reusable examples under `examples/skills/<skill-name>/`.
- Use `.template` for example code or config files so editors and tooling do not
  treat them as live project files.
- Do not add dependencies, application code, queues, services, or UI unless a
  separate implementation task explicitly calls for it.

---

## Choose the Target

| Skill Type | Target |
|------------|--------|
| UI, Gradio, visual QA, frontend workflow | `.trellis/spec/frontend/` |
| Backend, model runtime, API, storage workflow | `.trellis/spec/backend/` |
| Cross-cutting development workflow | `.trellis/spec/guides/` |
| Documentation-only workflow | `.trellis/spec/guides/` or `.trellis/workflow.md` |
| Test workflow for the Gradio app | `.trellis/spec/frontend/` plus related backend guide when inference/logging is involved |

If a skill spans multiple targets, write the stable cross-cutting contract in
`.trellis/spec/guides/` and link from the affected target indexes only when the
target has concrete rules to follow.

---

## Integration Steps

1. Read the skill's `SKILL.md`.
2. Identify the project target and any affected existing guides.
3. Extract only durable rules: triggers, contracts, required checks, examples,
   caveats, and forbidden patterns.
4. Add a focused guide section or a new guide file.
5. Add example templates only when they help future agents apply the rule.
6. Update the relevant `index.md`.
7. Report what changed, what was intentionally not integrated, and whether code
   was touched.

---

## What to Extract

| Extract | Keep It Project-Specific |
|---------|--------------------------|
| Trigger conditions | When Pixloom agents should use the skill |
| Contracts | Files, formats, naming, validation, review gates |
| Caveats | Differences from the generic skill in this repo |
| Examples | Minimal templates that match Pixloom's current stack |
| Checks | Commands or manual verification expected after changes |

Avoid copying long generic prose from the source skill. Convert it into rules
that a future agent can execute in this repository.

---

## Example File Rules

Use this layout when examples are useful:

```text
.trellis/spec/{target}/examples/skills/<skill-name>/
|-- README.md
|-- example.py.template
|-- config.template
```

Rules:
- `README.md` may be a normal markdown file.
- Code examples must use `.template`.
- Config examples must use `.template`.
- Do not import or execute files from `examples/`.

---

## Checklist

Before finishing:
- [ ] The target guide explains when to use the integrated skill.
- [ ] The guide states how Pixloom adapts or limits the generic skill behavior.
- [ ] The relevant `index.md` links the new guide.
- [ ] Any example code/config uses `.template`.
- [ ] No product code changed unless the user separately requested implementation.
- [ ] The final report lists changed files and verification.
