# Friend Setup

Use this when a new teammate joins the hackathon work.

## 1. Clone the control repo

```bash
git clone https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs.git
cd hack-6a0e416e-adlabs
```

This repo is the team control center: prompts, workflow, commit rules, and subagent playbooks.

## 2. Create a personal branch

Never work directly on `main`.

```bash
git switch -c <name>/<role>-setup
```

Examples:

```bash
git switch -c arman/frontend-setup
git switch -c dias/backend-setup
git switch -c aya/ml-setup
```

## 3. Pick your role

Use one of these roles:

| Role | Use when |
| --- | --- |
| `frontend` | UI, pages, components, styling |
| `backend` | API, database, auth, integrations |
| `ml` | prompts, model logic, evaluation, datasets |
| `docs-pitch` | README, demo script, presentation |
| `git-manager` | branches, commits, merge hygiene |
| `architect` | repo boundaries and technical decisions |
| `reviewer` | review only |

## 4. Use subagents

Before a big request, run the local router:

```bash
./scripts/route-task "describe your task"
```

It does not call any AI model, so it costs zero tokens. It returns:

- owner agent;
- model tier;
- target repo;
- whether reviewer is needed;
- the next prompt to send to Codex.

If the result is unclear, send this to Codex:

```text
Read AGENTS.md, TEAM_WORKFLOW.md, PROMPTS.md, SUBAGENTS.md, and MULTI_REPO_STRATEGY.md.

Act as triage-agent first:
- classify my request
- choose owner_agent
- choose model_tier: cheap | balanced | strongest
- list exact files/repos needed
- tell me whether to spawn frontend/backend/ml/reviewer subagents

Request:
<your request>
```

For direct subagent work, use prompts from `SUBAGENTS.md`.

## 5. Commit every hour

Run:

```bash
TEAM_MEMBER=<name> TEAM_ROLE=<role> ./scripts/team-commit "short summary"
```

Examples:

```bash
TEAM_MEMBER=arman TEAM_ROLE=frontend ./scripts/team-commit "built dashboard shell"
TEAM_MEMBER=dias TEAM_ROLE=backend ./scripts/team-commit "added cases API"
TEAM_MEMBER=aya TEAM_ROLE=ml ./scripts/team-commit "tested routing prompts"
```

Then push:

```bash
git push -u origin HEAD
```

## 6. Token discipline

- Use `cheap` for summaries, docs cleanup, commit messages, and simple checks.
- Use `balanced` for normal coding.
- Use `strongest` for architecture, hard bugs, security, and final review.
- Do not paste huge files into prompts; ask Codex to inspect paths locally.
- Keep stable rules in this repo so every teammate reuses the same context.
