# Domain Docs

This repository uses a single-context layout.

## Layout

- Root `CONTEXT.md` contains the project-wide domain language and operating notes.
- `docs/adr/` contains architectural decision records.

## Consumer rules

- Read `CONTEXT.md` first when you need project vocabulary or behavioral context.
- Read ADRs when you need historical decisions, tradeoffs, or constraints that affect design changes.
- Prefer the smallest relevant set of docs instead of scanning everything.
- If a change introduces a new durable decision, add an ADR rather than burying it in prose.

## Maintenance rules

- Keep `CONTEXT.md` short and current.
- Keep ADRs focused on one decision each.
- If the repository ever grows multiple independently documented subprojects, switch this file to a `CONTEXT-MAP.md` based layout.