# API

This file defines the public surface that should remain stable unless there is a deliberate compatibility change.

## Public Functions

### `auto()`

Enables AST-based automatic tracing for the current script.

### `capture(max_nodes=300, include_private=False, include_containers=None, focus_vars=None, pointer_watchers=None)`

Manually records a snapshot at the current execution point.

### `watch_vars(*names)`

Marks variable names that should always be observed. Also works as a decorator for function-scoped watch lists.

### `bind_fields(obj, **field_specs)`

Groups fields for animation and field-aware visualization.

### `set_mode(mode=None)`

Controls capture granularity.

- `None` defaults to `fine`.
- Supported values: `coarse`, `fine`, `line`.

### `set_layout(layout)`

Sets the layout configuration used by the renderer.

### `set_text_flow(flow)`

Controls text flow direction.

- Supported values: `horizontal`, `vertical`.

### `enable_breakpoints()` / `disable_breakpoints()`

Turns replay breakpoints on or off.

## Compatibility Rules

- Keep the above names stable unless the change is accompanied by a deprecation note and a migration path.
- Keep examples in `README.md` and other user-facing docs aligned with this list.
- Prefer additive changes over rename/removal.

## Internal Surface

Modules such as the scheduler, graph builder, AST hook, and renderer are implementation details. They can change during refactors, but changes that affect replay semantics should be reflected in `DESIGN.md` or an ADR.