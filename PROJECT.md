# PROJECT

DSVis is a Python data-structure visualization tool for students and instructors. The user experience should stay simple: import the package, run the program, and get an interactive replay view with minimal setup.

## What DSVis Is

- A teaching-oriented visualization library.
- A runtime that captures program state as execution progresses.
- A single-file HTML output that can be opened locally without extra services.

## What DSVis Is Not

- Not a general-purpose debugger implementation.
- Not a server-backed web application.
- Not a tool that mutates the user's data structures during capture.

## User Promise

The project should stay portable and easy to embed in a user's own repository. The common path should remain: `import dsvis`, enable tracing, run the algorithm, inspect the replay.

## Core Pipeline

```text
Python code
  -> AST hook / trigger
  -> scheduler
  -> raw steps
  -> display steps
  -> self-contained HTML replay
```

## Design Goal

Prefer clarity, stability, and educational value over feature breadth. When there is a trade-off, keep the replay semantics easy to understand and hard to break.