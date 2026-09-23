# Multi-Repo Strategy

The team should use separate implementation repositories for frontend, backend, and ML to reduce merge conflicts and keep Codex context small.

## Repository layout

| Repo | Purpose | Owner role |
| --- | --- | --- |
| `hack-6a0e416e-adlabs` | control center: workflow, prompts, docs, subagent rules | `git-manager`, `architect`, `docs-pitch` |
| `hack-6a0e416e-adlabs-frontend` | web/mobile UI | `frontend` |
| `hack-6a0e416e-adlabs-backend` | API, auth, database, integrations | `backend` |
| `hack-6a0e416e-adlabs-ml` | prompts, model router, evaluation, datasets | `ml` |

## Why split repos

- Frontend, backend, and ML agents do not fight over the same files.
- Each Codex session can load only the repo it needs.
- Hourly commits stay readable.
- Deployment can be separated by service.
- Final demo stays easier to explain: UI calls API, API calls ML/model router.

## Integration contract

Keep shared contracts in this control repo under `contracts/`.

Recommended files:

```text
contracts/api.md
contracts/events.md
contracts/model-routing.md
contracts/env.md
```

Rules:

- Frontend reads API contracts before UI integration.
- Backend updates contracts when API behavior changes.
- ML updates model-routing contracts when prompt/model behavior changes.
- Architect reviews contract changes before cross-repo implementation.

## Suggested GitHub repos

Create these under `BAITC-Hacks`:

```text
https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-frontend
https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-backend
https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-ml
```

## Subagent routing

| Task | Repo | Agent | Model tier |
| --- | --- | --- | --- |
| UI screens, components, styling | frontend repo | `frontend` | `balanced` |
| API/database/auth | backend repo | `backend` | `balanced` |
| Prompt routing, model selection, evals | ML repo | `ml` | `balanced` or `strongest` |
| API contract changes | control repo | `architect` | `strongest` |
| README, pitch, demo script | control repo | `docs-pitch` | `cheap` |
| Final review | all repos | `reviewer` | `strongest` |

## Setup commands

Frontend:

```bash
git clone https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-frontend.git
cd hack-6a0e416e-adlabs-frontend
git switch -c <name>/frontend-work
```

Backend:

```bash
git clone https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-backend.git
cd hack-6a0e416e-adlabs-backend
git switch -c <name>/backend-work
```

ML:

```bash
git clone https://github.com/BAITC-Hacks/hack-6a0e416e-adlabs-ml.git
cd hack-6a0e416e-adlabs-ml
git switch -c <name>/ml-work
```

## Merge rule

Do not merge cross-repo changes until contracts are updated in this control repo.

