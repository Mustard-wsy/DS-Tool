# DSVis Context

DSVis is a Python data-structure visualization tool for teaching and demonstration. The project is designed to be portable, easy to import, and safe to embed in a user's own codebase without extra runtime services.

## Read Order

- `PROJECT.md` for the project goal and non-goals.
- `ARCHITECTURE.md` for the layer map and runtime flow.
- `DESIGN.md` for the core design principles.
- `API.md` for the stable public surface.
- `ROADMAP.md` for the intended direction of travel.
- `docs/adr/` for durable decisions.

## Working Vocabulary

- Raw timeline: every recorded execution event.
- Display timeline: the user-facing subset shown in the UI.
- Raw step: the smallest recorded snapshot.
- Display step: a replay anchor derived from raw steps.
- `auto()`: entry point for AST-based automatic tracing.
- `capture()`: manual snapshot entry point.
- Breakpoints: UI navigation markers, not a separate execution engine.

## Current Constraints

- Do not mutate user objects during snapshot.
- Keep the output self-contained HTML.
- Preserve public API compatibility unless a deprecation plan is added first.
- Keep the documentation focused on teaching-oriented playback, not on general debugger semantics.