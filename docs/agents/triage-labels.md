# Triage Labels

This repository uses the default label vocabulary.

## Canonical labels

- `needs-triage` means a maintainer still needs to evaluate the issue.
- `needs-info` means the issue is waiting on reporter input.
- `ready-for-agent` means the issue is fully specified and safe for an AFK agent to pick up.
- `ready-for-human` means the issue needs human implementation.
- `wontfix` means the issue will not be actioned.

## Usage rules

- Use these exact strings when a skill needs to classify an issue.
- Do not invent alternate synonyms unless the repository introduces them explicitly later.
- If the local markdown workflow adds status fields or frontmatter, map those fields back to these five roles instead of duplicating the vocabulary.

## Default posture

If a skill does not have a better signal, it should assume the labels above are available exactly as written.