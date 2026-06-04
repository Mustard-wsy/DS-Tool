# DSVis Debugger Semantics

This document defines the replay debugger model used by DSVis. The core design goal is to keep execution semantics and presentation semantics separate.

## 1. Core model

DSVis is a replay-based debugger, not a live tracing debugger. A user program is executed once with AST-injected triggers. During that run, the system records a linear execution history. The frontend later replays that history.

The model has two timelines:

- **Raw Timeline**: the true execution timeline made of Raw Steps
- **Display Timeline**: a derived presentation timeline made of Display Steps

All debugger control-flow behavior is defined on the Raw Timeline. Display Steps are only anchors for browsing and teaching-oriented navigation.

## 2. Step taxonomy

### Raw Step

A Raw Step is the smallest recorded execution snapshot.

Properties:

- produced by `trigger()`
- anchored to one source location: `(filename, lineno)`
- contains a stack snapshot and object-graph snapshot
- represents a single replay atom on the Raw Timeline

Raw Steps are not presentation units. Multiple Raw Steps may be grouped into one Display Step depending on the current mode.

### Display Step

A Display Step is a user-visible replay anchor.

Properties:

- derived from Raw Steps
- mode-dependent
- used by the presentation layer to expose keyframes and browsing entry points
- may correspond to one Raw Step or a group of Raw Steps

Display Steps do not define control-flow semantics.

## 3. Position state

The debugger maintains a current Raw Position.

The current Display Position is derived from the current Raw Position and the active mode’s Display Step mapping.

Recommended invariant:

- `currentRawIndex` is the canonical position
- `currentDisplayIndex` is derived from `currentRawIndex`

## 4. Breakpoints

DSVis uses line breakpoints only.

Breakpoint semantics:

- a breakpoint is set by clicking a source line in the code panel
- a breakpoint matches a Raw Step whose top frame location equals the breakpoint location `(filename, lineno)`
- breakpoint hits are evaluated during replay, not during live execution
- the debugger pauses before the Raw Step that would execute the matched location

This is an execution-before pause model.

## 5. Control-flow commands

### Continue / Resume

Continue replay on the Raw Timeline until one of the following occurs:

- a breakpoint is about to be hit
- the user pauses playback
- the timeline ends

### Pause

Stop automatic replay at the current Raw Position without resetting the session.

### Step Into

Advance to the next Raw Step that changes the visible source-line state.

This is the smallest-granularity debugger action.

### Step Over

Advance according to control-flow semantics in the current frame.

Rules:

- do not enter called functions
- stop at the next boundary visible to the current frame
- do not depend on Display Step boundaries

### Step Out

Continue replay until the current frame returns, then stop in the caller frame.

The stopping point is after the return, at the first replay position available in the caller context.

### Restart

Re-run the user program and rebuild the full replay history from scratch.

### Stop

Terminate the current debug session and close the replay UI.

## 6. Presentation commands

These commands operate on the Display Timeline only.

The code panel's arrow and current-line highlight may point at the next executable source line derived from the current Raw Position. This is a presentation choice only and does not change Raw Timeline semantics.

### Next Display Step

Move to the next Display Step anchor.

### Previous Display Step

Move to the previous Display Step anchor.

### Jump to Display Step

Jump directly to a selected Display Step anchor.

Presentation commands do not redefine control-flow semantics and do not alter the Raw Timeline.

## 7. Auto-run

Auto-run is a replay mode that advances Raw Steps at a fixed speed.

It stops when:

- the next breakpoint boundary is reached
- the user pauses playback
- the timeline ends

Auto-run is semantically equivalent to repeated Continue actions with timed advancement.

## 8. Invariants

- Breakpoints are line breakpoints only
- Breakpoint pauses happen before the next Raw Step that would hit the breakpoint line/frame
- Control-flow commands act on the Raw Timeline
- Presentation commands act on the Display Timeline
- Display Step is derived from Raw Step, not the other way around

## 9. Intentional differences from live debuggers

DSVis intentionally differs from a live debugger in the following ways:

- execution is recorded first, then replayed
- the debugger UI does not control CPython tracing in real time
- Display Steps are presentation anchors rather than execution atoms
- the replay engine may derive multiple presentation modes from the same Raw Timeline

## 10. Button summary

- `Continue` / `Resume`: replay on the Raw Timeline until the next stop condition
- `Pause`: stop automatic replay without resetting state
- `Step Over`: control-flow step that does not enter callees
- `Step Into`: advance one Raw Step
- `Step Out`: run until the current frame returns
- `Restart`: rebuild the replay session
- `Stop`: end the session
- `Toggle Breakpoints`: enable or disable breakpoint hits globally
- `Next Display Step`: move to the next Display Step
- `Previous Display Step`: move to the previous Display Step
- `Jump to Display Step`: jump to a chosen Display Step

## 11. Node field visibility

The settings panel provides per-field visibility toggles scoped globally by type and field name. This is a pure presentation feature — it does not alter the Raw Timeline or control-flow semantics.

### Field key system

Every row in a graph node carries a `field_key` of the form `Type::fieldName` (produced by the backend). The frontend normalises `::` to `.` for the global visibility key `Type.field`.

### Cascade-hide semantics

When a field is hidden:
1. The corresponding row is removed from the owning node card.
2. If the row is a `ref` (references another node), the outgoing edge is hidden.
3. If the target node has no remaining incoming edges after edge filtering, it is hidden too (cascade).

This applies uniformly across all instances of the same type — hiding `Parent.a` hides field `a` on every `Parent` node in the graph.

Parent-field cascade: hiding a field key like `GraphNode.neighbors` also hides all sub-item keys like `GraphNode.neighbors[0]`, `GraphNode.neighbors[1]`, etc. The reverse is not true — hiding an individual item does not hide the parent field. This also applies to dict-style keys: hiding `Graph.nodes` hides `Graph.nodes['A']`, `Graph.nodes['B']`, etc.

### Node-level hide (right-click → hide)

Right-clicking a node and selecting "hide" removes the node and all its descendant nodes (nodes reachable via outgoing edges). This is a presentation-only operation:

1. The hidden node and all transitively reachable nodes are added to `HIDDEN_NODES`.
2. `filterHiddenNodes()` computes the transitive closure of `HIDDEN_NODES` over outgoing edges before filtering.
3. Restoring a parent does **not** auto-restore descendants — each node is independently toggleable via the hidden-nodes panel.