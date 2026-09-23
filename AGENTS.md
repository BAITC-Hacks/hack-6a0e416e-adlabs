# HackAlemAI Codex Team Rules

These rules apply to the whole repository.

## Operating mode

- Start every non-trivial task with triage: classify the task, choose the smallest useful context, and decide whether a reviewer is needed.
- Prefer focused edits in the owner's area instead of broad refactors.
- Do not touch another teammate's area unless the task explicitly requires it.
- Keep prompts short and point Codex to the relevant files instead of pasting the whole repository.
- Commit at least once per hour using `scripts/team-commit`.

## Agent roles

- `triage`: routes requests to the right role and model tier.
- `architect`: designs data models, APIs, system boundaries, and risky decisions.
- `frontend`: works in `frontend/`, `app/`, `src/app/`, `src/components/`, `src/pages/`, `src/styles/`, `public/`, and UI config files.
- `backend`: works in `backend/`, `server/`, `api/`, `src/server/`, and database logic.
- `ml`: works in `ml/`, `prompts/`, `evals/`, `datasets/`, and model-routing logic.
- `reviewer`: checks correctness, regressions, security, and missing tests; does not commit code changes.
- `docs-pitch`: writes README, demo script, pitch, diagrams, and changelog.
- `git-manager`: keeps branches clean, commits hourly, and resolves workflow issues.

## Model routing policy

- Use the cheapest/fastest model for copy edits, simple docs, small CSS tweaks, commit messages, and summaries.
- Use a balanced model for normal feature implementation, tests, refactors, and bug fixes with limited scope.
- Use the strongest model for architecture, ambiguous bugs, security, cross-module changes, database design, and final review.

## Git rules

- Never work directly on `main` unless the team lead explicitly allows it.
- Use branch format: `<name>/<area>-<short-task>`, for example `armatis/frontend-dashboard`.
- Keep one owner per feature branch.
- Before committing, run `git status --short` and review the staged files.
- Set `TEAM_ROLE` explicitly when using `scripts/team-commit`.
- Do not use destructive git commands such as `git reset --hard` or `git checkout -- <file>` unless the team lead explicitly asks.
