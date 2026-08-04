# Issue Tracker

This repository uses local markdown as the issue tracker.

## Where issues live

Create one folder per issue under `.scratch/<issue-slug>/`.

Recommended files for each issue:

- `issue.md` for the problem statement and acceptance criteria
- `notes.md` for triage or investigation notes
- `plan.md` for implementation steps, if needed

## Working rules

- Treat `.scratch/` as the source of truth for open work.
- Keep each issue folder self-contained so it can be moved or archived easily.
- Use a short, stable slug for the folder name.
- Prefer markdown headings and short checklists over ad hoc plain text.

## Typical workflow

1. Create a new folder in `.scratch/` for the issue.
2. Write the issue summary and expected behavior in `issue.md`.
3. Add notes as triage or implementation details change.
4. Close the issue by updating the markdown and moving or archiving the folder if the repo adopts that convention later.

## Notes for skills

Skills that expect an issue tracker should read from and write to `.scratch/<issue-slug>/` instead of calling a hosted issue API.