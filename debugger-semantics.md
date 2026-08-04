# DSVis Debugger and Presentation Semantics

This document defines DSVis replay-debugger semantics and the intended split between Python runtime collection and browser-side presentation. The strategic goal is: user code should normally only import DSVis and call `dsvis.auto()`. Layout, field visibility, edge proxying, title replacement, and AI-assisted page changes belong to the generated frontend.

## 1. Core model

DSVis is a replay-based debugger, not a live tracing debugger. A user program is executed once with AST-injected triggers. During that run, DSVis records a linear execution history. The frontend later replays that history.

The model has two timelines:

- **Raw Timeline**: the true execution timeline made of Raw Steps.
- **Display Timeline**: a derived presentation timeline made of Display Steps.

All debugger control-flow behavior is defined on the Raw Timeline. Display Steps are presentation anchors for browsing and teaching-oriented navigation.

## 2. Raw data vs presentation data

A captured step should be treated as immutable runtime evidence. Frontend settings must not mutate the original captured step. Instead, rendering should be a pipeline:

1. Raw step payload from Python.
2. Presentation configuration: layout direction, text flow, visible fields, hidden nodes, title field, edge proxy rules, active preset.
3. Graph transform: hide rows/nodes, redirect proxy edges, compute title substitutions.
4. Layout/measurement data.
5. G6 render payload.

This separation is important because PageAgent and manual UI controls should modify presentation configuration, not the user's Python objects or recorded execution history.

## 3. Step taxonomy

### Raw Step

A Raw Step is the smallest recorded execution snapshot.

Properties:

- Produced by `trigger()`.
- Anchored to one source location: `(filename, lineno)`.
- Contains a stack snapshot and object-graph snapshot.
- Represents a single replay atom on the Raw Timeline.

Raw Steps are not presentation units. Multiple Raw Steps may be grouped into one Display Step depending on the current mode.

### Display Step

A Display Step is a user-visible replay anchor.

Properties:

- Derived from Raw Steps.
- Mode-dependent.
- Used by the presentation layer to expose keyframes and browsing entry points.
- May correspond to one Raw Step or a group of Raw Steps.

Display Steps do not define control-flow semantics.

## 4. Position state

The debugger maintains a current Raw Position.

The current Display Position is derived from the current Raw Position and the active mode’s Display Step mapping.

Recommended invariant:

- `currentRawIndex` is the canonical position.
- `currentDisplayIndex` is derived from `currentRawIndex`.

## 5. Breakpoints

DSVis uses line breakpoints only.

Breakpoint semantics:

- A breakpoint is set by clicking a source line in the code panel.
- A breakpoint matches a Raw Step whose top frame location equals the breakpoint location `(filename, lineno)`.
- Breakpoint hits are evaluated during replay, not during live execution.
- The debugger pauses before the Raw Step that would execute the matched location.

This is an execution-before pause model.

## 6. Control-flow commands

### Continue / Resume

Continue replay on the Raw Timeline until one of the following occurs:

- A breakpoint is about to be hit.
- The user pauses playback.
- The timeline ends.

### Pause

Stop automatic replay at the current Raw Position without resetting the session.

### Step Into

Advance to the next Raw Step that changes the visible source-line state.

### Step Over

Advance according to control-flow semantics in the current frame.

Rules:

- Do not enter called functions.
- Stop at the next boundary visible to the current frame.
- Do not depend on Display Step boundaries.

### Step Out

Continue replay until the current frame returns, then stop in the caller frame.

The stopping point is after the return, at the first replay position available in the caller context.

### Restart

Re-run the user program and rebuild the full replay history from scratch.

### Stop

Terminate the current debug session and close the replay UI.

## 7. Presentation commands

These commands operate on the Display Timeline only.

The code panel's arrow and current-line highlight may point at the next executable source line derived from the current Raw Position. This is a presentation choice only and does not change Raw Timeline semantics.

### Next Display Step

Move to the next Display Step anchor.

### Previous Display Step

Move to the previous Display Step anchor.

### Jump to Display Step

Jump directly to a selected Display Step anchor.

Presentation commands do not redefine control-flow semantics and do not alter the Raw Timeline.

## 8. Auto-run

Auto-run is a replay mode that advances Raw Steps at a fixed speed.

It stops when:

- The next breakpoint boundary is reached.
- The user pauses playback.
- The timeline ends.

Auto-run is semantically equivalent to repeated Continue actions with timed advancement.

## 9. Node field visibility

The settings panel provides per-field visibility toggles scoped globally by type and field name. This is a pure presentation feature: it does not alter the Raw Timeline or control-flow semantics.

### Field key system

Every row in a graph node carries a `field_key` of the form `Type::fieldName` produced by the backend. The frontend normalizes `::` to `.` for the global visibility key `Type.field`.

Field keys should prefer stable class names over import-context-dependent module-qualified names. This keeps presets such as `BTreeNode.keys` valid whether a script runs as `__main__` or is imported by tests.

### Cascade-hide semantics

When a field is hidden:

1. The corresponding row is removed from the owning node card.
2. If the row is a `ref`, the outgoing edge is hidden.
3. If the target node has no remaining incoming edges after edge filtering, it is hidden too.

Parent-field cascade: hiding a field key like `GraphNode.neighbors` also hides sub-item keys like `GraphNode.neighbors[0]`, `GraphNode.neighbors[1]`, etc. The reverse is not true.

### Node-level hide

Right-clicking a node can hide only that node or hide the node and descendants reachable through outgoing edges. This is presentation-only state and should be reversible through the hidden-nodes panel.

## 10. Edge proxy semantics

Edge proxying is a frontend presentation transform. It exists to make structures such as B-Tree and B+Tree render like textbook diagrams without requiring Python-side binding code.

A proxy rule has this shape:

```text
Target ref field: Type.children
Proxy value field: Type.keys
Ratio: number or auto
Include ends: boolean
```

Expected behavior:

- Original object graph edges remain attached to `children[...]` in raw data.
- During presentation transform, visible edge ports may be computed from `keys[...]` or synthetic key slots.
- The transform must keep enough metadata for layout and debugging logs to explain why an edge was redirected.
- Proxy rules should be editable by users and PageAgent through frontend APIs, not Python helper calls.

## 11. PageAgent / AI integration contract

The AI assistant should operate through a narrow, explicit frontend API instead of scraping arbitrary DOM whenever possible. The proposed namespace is `window.DSVisAgentAPI`.

Recommended read APIs:

- `getCurrentStepSummary()` — current raw/display index, source line, active frame.
- `getGraphSchema()` — node classes, fields, row kinds, field keys.
- `getPresentationConfig()` — text flow, hidden fields, edge proxy rules, title field, active preset.
- `getRenderDiagnostics()` — warnings/errors from the latest graph transform and render pass.

Recommended write APIs:

- `applyPreset(id)`.
- `setTextFlow("horizontal" | "vertical")`.
- `setFieldVisibility(fieldKey, "visible" | "self" | "cascade")`.
- `setTitleField(className, fieldKey | null)`.
- `setEdgeProxy(targetKey, rule | null)`.
- `restoreHiddenNode(nodeId)`.

All write APIs should validate input and emit structured logs. PageAgent can still see the page, but stable APIs make it less fragile and easier to test.

## 12. Logging requirements

DSVis should have two coordinated logging layers.

### Python logging

Use Python's standard `logging` package with module-level loggers:

- `dsvis.runtime.ast_hook`
- `dsvis.runtime.scheduler`
- `dsvis.graph_builder`
- `dsvis.card_renderer`

The log level should be configurable with an environment variable such as `DSVIS_LOG_LEVEL`.

### Frontend logging

Use a small frontend logger wrapper instead of direct scattered `console.log` calls. Suggested channels:

- `agent` — PageAgent load/init and agent API calls.
- `transform` — field visibility, edge proxy, title replacement.
- `layout` — measured sizes, G6 layout options.
- `render` — render lifecycle and failures.

Logs should be structured objects where possible, for example:

```js
DSVisLogger.debug('transform', 'edge-proxy-applied', {
  source: edge.source,
  target: edge.target,
  from: 'BTreeNode.children[1]',
  to: 'BTreeNode.keys[0]',
});
```

## 13. Template split plan

`dsvis/template.html` is currently a large single-file frontend. The generated artifact may remain a self-contained HTML file, but source should be split into modules.

Suggested modules:

- `state.js` — current step, UI state, persisted settings.
- `agent_api.js` — `window.DSVisAgentAPI` read/write methods.
- `page_agent_adapter.js` — PageAgent loading and custom/default model configuration.
- `graph_transform.js` — hidden fields, edge proxy, title substitution, diff decoration.
- `g6_renderer.js` — G6 registration, port resolution, render/update lifecycle.
- `settings_panel.js` — manual visual configuration UI.
- `debug_controls.js` — step controls, breakpoints, auto-run.
- `logger.js` — frontend logging wrapper.

This split should be source-level first. A later packaging step can inline the modules into the HTML if the zero-install distribution requirement remains important.

## 14. Intentional differences from live debuggers

DSVis intentionally differs from a live debugger in the following ways:

- Execution is recorded first, then replayed.
- The debugger UI does not control CPython tracing in real time.
- Display Steps are presentation anchors rather than execution atoms.
- The replay engine may derive multiple presentation modes from the same Raw Timeline.

## 15. Button summary

- `Continue` / `Resume`: replay on the Raw Timeline until the next stop condition.
- `Pause`: stop automatic replay without resetting state.
- `Step Over`: control-flow step that does not enter callees.
- `Step Into`: advance one Raw Step.
- `Step Out`: run until the current frame returns.
- `Restart`: rebuild the replay session.
- `Stop`: end the session.
- `Toggle Breakpoints`: enable or disable breakpoint hits globally.
- `Next Display Step`: move to the next Display Step.
- `Previous Display Step`: move to the previous Display Step.
- `Jump to Display Step`: jump to a chosen Display Step.
