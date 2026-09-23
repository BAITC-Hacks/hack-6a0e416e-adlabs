# Subagent Playbook

Use this file when you want Codex agents to work in parallel without wasting tokens.

## Zero-token routing

Run the local router before asking a model:

```bash
./scripts/route-task "describe the task"
```

Use the returned `next_prompt` for the selected agent.

## Model tiers

| Tier | Use for | Suggested model |
| --- | --- | --- |
| `cheap` | summaries, docs cleanup, simple git checks, small copy/UI text changes | fast/efficient model |
| `balanced` | normal implementation, tests, medium bug fixes | balanced coding model |
| `strongest` | architecture, hard debugging, security, final review | current strongest parent model |

Do not send every task to the strongest model. Start cheap, escalate only when needed.

## Default routing

| Request | Agent | Tier |
| --- | --- | --- |
| "What should we build?" | `architect` | `strongest` |
| "Implement this page/component" | `frontend` | `balanced` |
| "Implement API/database logic" | `backend` | `balanced` |
| "Improve prompts/model routing/evals" | `ml` | `balanced` or `strongest` |
| "Check if this is correct" | `reviewer` | `strongest` |
| "Write README/pitch/demo" | `docs-pitch` | `cheap` or `balanced` |
| "Commit/check branch/status" | `git-manager` | `cheap` |

## Subagent launch prompts

### Triage

```text
You are triage-agent for our HackAlemAI team.

Classify the request and return:
1. task_type
2. owner_agent
3. model_tier: cheap | balanced | strongest
4. exact files/directories needed
5. whether implementation can start now
6. whether reviewer is needed
7. the next prompt to send to the selected agent

Request:
<request>
```

### Frontend worker

```text
You are frontend-agent.

Work only in frontend-owned files unless the task explicitly requires otherwise.
Implement:
<task>

Rules:
- keep the patch focused
- do not edit backend/docs/git workflow files
- run the smallest useful check
- return changed files and verification result
```

### Backend worker

```text
You are backend-agent.

Work only in backend-owned files unless the task explicitly requires otherwise.
Implement:
<task>

Rules:
- keep API/data changes small
- add validation where needed
- do not edit frontend/docs/git workflow files
- run the smallest useful check
- return changed files and verification result
```

### ML worker

```text
You are ml-agent.

Work only in ML-owned files unless the task explicitly requires otherwise.
Implement:
<task>

Rules:
- keep prompt/model-router changes measurable
- document expected inputs and outputs
- add small eval examples where useful
- do not edit frontend/backend workflow files
- return changed files and verification result
```

### Reviewer

```text
You are reviewer-agent.

Review the current branch for:
- correctness bugs
- regressions
- security/data risks
- missing checks
- out-of-scope files for the assigned role

Return findings first, ordered by severity.
Do not rewrite code unless asked.
```

### Docs and pitch

```text
You are docs-pitch-agent.

Create or improve hackathon-facing materials:
<task>

Make it judge-friendly:
- problem
- solution
- AI value
- demo flow
- impact
- technical architecture
```

### Git manager

```text
You are git-manager-agent.

Check:
- current branch
- changed files
- whether files match TEAM_ROLE ownership
- whether hourly commit is due
- the safest next git command

Do not run destructive commands.
```

## Parallel work pattern

Use subagents only when their work does not overlap:

- `frontend` edits UI files.
- `backend` edits API/server files.
- `docs-pitch` edits docs/pitch files.
- `reviewer` reviews after a meaningful patch.
- `git-manager` checks branches and commit discipline.

If two agents need the same file, stop and ask `architect` to split ownership first.
