# ARCHITECTURE

This document describes the current layer split in DSVis and the boundaries that should stay stable during refactors.

## Layer Map

- Public API: `dsvis/__init__.py`, `dsvis/dsvis.py`
- Runtime capture: `dsvis/runtime/ast_hook.py`, `dsvis/runtime/injector.py`, `dsvis/runtime/trigger.py`
- Scheduling and state: `dsvis/runtime/scheduler.py`, `dsvis/runtime/config.py`
- Snapshot building: `dsvis/graph_builder.py`, `dsvis/stack_serializer.py`, `dsvis/introspection.py`, `dsvis/field_binding.py`
- Rendering: `dsvis/card_renderer.py`, `dsvis/template.html`, `dsvis/styles.css`

## Runtime Flow

### Auto mode

```text
user script -> auto() -> AST hook -> injected trigger() calls -> scheduler -> snapshot -> HTML flush
```

### Manual capture

```text
user code -> capture() -> scheduler -> snapshot -> HTML flush
```

## Boundary Rules

- The runtime layer collects data; it should not know frontend rendering details.
- The renderer layer formats captured data; it should not mutate runtime state.
- Snapshot builders should only read user objects.
- Breakpoints are a navigation concern in the replay UI, not a separate execution engine.

## Timeline Model

- Raw timeline: every recorded step.
- Display timeline: the filtered playback view shown to the user.
- The UI may navigate between display steps while still keeping raw steps available for control-flow actions.

## Why This Split Matters

Refactors should stay local to one layer whenever possible. If a change crosses a layer boundary, it should be explicit in the design document or recorded as an ADR.