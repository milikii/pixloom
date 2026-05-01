<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

Use the `/trellis:start` command when starting a new session to:
- Initialize your developer identity
- Understand current project context
- Read relevant guidelines

Use `@/.trellis/` to learn:
- Development workflow (`workflow.md`)
- Project structure guidelines (`spec/`)
- Developer workspace (`workspace/`)

If you're using Codex, project-scoped helpers may also live in:
- `.agents/skills/` for reusable Trellis skills
- `.codex/agents/` for optional custom subagents

Keep this managed block so 'trellis update' can refresh the instructions.

<!-- TRELLIS:END -->

## Local Note

- In `Claude Code`, start Trellis with `/trellis:start`.
- In `Codex`, Trellis appears as project skills rather than a single `trellis` menu entry.
- Use `$start`, `$brainstorm`, `$check`, `$check-cross-layer`, `$finish-work`, `$record-session`, and `$parallel` in `Codex`.
