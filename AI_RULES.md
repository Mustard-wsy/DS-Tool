# AI RULES

These rules are for automated contributors and refactoring assistants working on DSVis.

## Before Editing

- Read `CONTEXT.md` first.
- Read `PROJECT.md`, `ARCHITECTURE.md`, `DESIGN.md`, and `API.md` before large edits.
- Prefer the smallest relevant slice of code or documentation.

## Hard Constraints

- Do not mutate user objects during snapshot collection.
- Do not change public API names without an explicit compatibility plan.
- Do not introduce a new frontend framework or a server dependency just to solve a local problem.
- Do not let renderer code reach back into runtime state.

## Refactor Rules

- Prefer small, reversible changes.
- Keep behavior changes separate from structural cleanup when possible.
- If a change affects replay semantics, step logic, or breakpoint behavior, update the docs at the same time.
- If a decision is durable, record it in `docs/adr/` instead of burying it in prose.

## Review Rules

- Verify that examples still match the documented API.
- Prefer explicit compatibility notes over silent behavior changes.
- When in doubt, stop at the architecture boundary and ask for confirmation.