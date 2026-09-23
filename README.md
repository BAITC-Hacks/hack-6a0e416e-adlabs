# hack-6a0e416e-adlabs
Hackathon team repository for ADLabs

## Team workflow

- Team rules: `AGENTS.md`
- Workflow: `TEAM_WORKFLOW.md`
- Prompt library: `PROMPTS.md`
- Subagent playbook: `SUBAGENTS.md`
- Friend setup: `FRIEND_SETUP.md`
- Multi-repo strategy: `MULTI_REPO_STRATEGY.md`
- Hourly commit helper: `scripts/team-commit`
- Task router: `scripts/route-task`

## Repository role

This repository contains the Career Quest MVP in one monorepo: `frontend/` (React, TypeScript, Vite), `backend/` (FastAPI), `ml/` (deterministic recommendation engine), `datasets/`, and the shared `contracts/`. `MULTI_REPO_STRATEGY.md` describes an earlier team strategy; this MVP runs from this repository.

## Quick route

Before spending model tokens on a large task, run:

```bash
./scripts/route-task "build login page"
```

It returns the suggested agent, model tier, target repo, and next prompt.

## Career Quest MVP: local run on Windows

Use PowerShell in the repository root (the folder containing this README). Python 3.11 or newer and Node.js 20.19 or newer are required. The local setup was checked with Python 3.14.0, Node.js 24.12.0, and npm 11.12.0. No Docker is needed.

First-time setup (skip the virtual environment creation if `.venv` already exists):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix frontend install
```

Start the API in one PowerShell window from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the web client in another PowerShell window from the same root:

```powershell
npm --prefix frontend run dev
```

Open `http://localhost:5173`. Check the API at `http://localhost:8000/api/health`; interactive API docs are at `http://localhost:8000/docs`. Vite forwards browser requests under `/api` to the local API, so no frontend URL setting is needed for this setup. Stop each process with Ctrl+C.

The default `AI_PROVIDER=template` answers AI Navigator questions deterministically from the profile, skill gap, recommendations, and roadmap. No API key is needed. Set `AI_PROVIDER=openai` with `OPENAI_API_KEY`, or `AI_PROVIDER=nvidia` with `NVIDIA_API_KEY`, to use an optional OpenAI-compatible chat completion adapter. `OPENAI_MODEL` and `NVIDIA_MODEL` override the defaults in `.env.example`. The adapter chooses a brief or contextual version assembled from computed facts; it cannot add new skills, events, dates, or forecasts. Rankings, projections, and evidence IDs remain deterministic. If the key is missing or the call fails, the template answer is returned. Keys come from process environment only; the app does not load `.env` automatically. For example, in PowerShell set `$env:AI_PROVIDER = 'template'` before starting the API.

## Demo path

1. Select employee `E0001` and enter Employee mode. The overview shows the target, readiness, key gap, first activity, and first roadmap step.
2. Open **Activities**, then **Подробнее и начать** on a recommendation. Review the dataset description, prerequisites, schedule, skill gains, forecast, and optional LMS link. Use **Записаться → Начать → Отметить выполненным**. The refreshed readiness, recommendations, roadmap, and activity history appear immediately. These status changes and skill gains live only in API memory. The repeatable `EV_036` can be enrolled again after completion.
3. Open **Roadmap** for up to three sequential steps and the full target skill map. Open **AI Navigator** for suggested questions or type your own. Answers include facts, reason, expected effect, limitation, next step, and source IDs.
4. Switch to HR overview from the sidebar for aggregate progress. To restore the initial demo state, restart the API.

Backend checks: `.\.venv\Scripts\python.exe -m pytest backend/tests tests -q --basetemp .pytest_local`. Frontend checks: `npm --prefix frontend run typecheck` and `npm --prefix frontend run build`.

MVP behavior, final gaps, and API contracts are documented in [docs/MVP_SPEC.md](docs/MVP_SPEC.md), [docs/FINAL_GAP_ANALYSIS.md](docs/FINAL_GAP_ANALYSIS.md), and [contracts/api.md](contracts/api.md). Simulated activity actions are held in server memory and reset when the API restarts.
