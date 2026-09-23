# HackAlemAI Team Workflow

This repo is optimized for a small team using 3 Codex subscriptions efficiently.

## Core idea

Every request goes through a quick triage before spending expensive tokens:

1. What type of task is this?
2. Which agent role should own it?
3. What is the cheapest model tier that can solve it safely?
4. Which files are relevant?
5. Does the result need review?

## Recommended account split

| Subscription | Primary role | Use for |
| --- | --- | --- |
| Account 1 | Architect + reviewer | architecture, risky decisions, final review |
| Account 2 | Builder | frontend, backend, tests, integrations |
| Account 3 | PM + docs | README, pitch, demo script, changelog, git hygiene |

## Branch strategy

Each teammate works in their own branch:

```bash
git switch -c <name>/<area>-<task>
```

Examples:

```bash
git switch -c arman/frontend-dashboard
git switch -c dias/backend-api
git switch -c aya/docs-pitch
```

Avoid multiple people editing the same files in the same hour. If two areas need the same file, ask `architect` or `git-manager` first.

## Ownership map

| Role | Primary files |
| --- | --- |
| `frontend` | `frontend/`, `app/`, `src/app/`, `src/components/`, `src/pages/`, `src/styles/`, `public/`, UI config files |
| `backend` | `backend/`, `server/`, `api/`, `src/server/`, database files |
| `ml` | `ml/`, `prompts/`, `evals/`, `datasets/`, model-routing files |
| `docs-pitch` | `README.md`, `docs/`, `pitch/`, `PROMPTS.md` |
| `git-manager` | `TEAM_WORKFLOW.md`, `team-logs/`, release notes |
| `architect` | `AGENTS.md`, `TEAM_WORKFLOW.md`, `docs/`, `contracts/`, `schemas/`, `architecture/`, cross-cutting decisions |
| `reviewer` | review only; no code commits unless explicitly approved |

If the project structure changes, update this table immediately.

## Hourly commit ritual

Every teammate runs this once per hour:

```bash
TEAM_MEMBER=<name> TEAM_ROLE=<role> ./scripts/team-commit "short summary"
```

Examples:

```bash
TEAM_MEMBER=arman TEAM_ROLE=frontend ./scripts/team-commit "dashboard layout"
TEAM_MEMBER=dias TEAM_ROLE=backend ./scripts/team-commit "created tasks API"
TEAM_MEMBER=aya TEAM_ROLE=docs-pitch ./scripts/team-commit "updated pitch draft"
```

The script:

- refuses empty messages;
- refuses to commit on `main` or `master`;
- requires a known `TEAM_ROLE`;
- blocks files outside the role's ownership area;
- writes a per-person log in `team-logs/<name>.md`;
- stages only the files it checked plus the per-person log;
- creates a timestamped commit.

If a cross-area change is intentional, ask `git-manager` or `architect`, then run:

```bash
TEAM_ALLOW_OUT_OF_SCOPE=1 TEAM_MEMBER=<name> TEAM_ROLE=<role> ./scripts/team-commit "short summary"
```

## Token saving rules

- Ask for one concrete result per prompt.
- Reference file paths instead of pasting files.
- Let Codex inspect the repo locally instead of uploading context manually.
- Use `reviewer` only after a meaningful change, not after every small edit.
- Keep stable instructions in `AGENTS.md`, `TEAM_WORKFLOW.md`, and `PROMPTS.md`.

## End-of-day merge flow

1. Each teammate pushes their branch.
2. `reviewer` checks the branch.
3. `git-manager` merges or opens a PR.
4. `docs-pitch` updates README and demo notes.
