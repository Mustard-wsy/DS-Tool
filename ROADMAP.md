# ROADMAP

This roadmap is intentionally lightweight. It exists to tell future refactors what direction the project is trying to move in.

## Near Term

- Stabilize the documentation set.
- Reduce ambiguity between raw replay semantics and display semantics.
- Keep the public API readable and import-friendly.

## Mid Term

- Separate concerns more cleanly between capture, scheduling, and rendering.
- Make compatibility guarantees easier to reason about.
- Keep the replay UI predictable for teaching use cases.

## Long Term

- Support the core data structures used in course work with a consistent visualization model.
- Preserve a small, embeddable footprint.
- Keep the project maintainable without requiring deep knowledge of every runtime module.

## Planning Rule

If a change is likely to affect user code, examples, or replay semantics, document it before implementation.