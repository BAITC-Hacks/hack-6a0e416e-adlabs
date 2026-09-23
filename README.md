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

The default `AI_PROVIDER=template` answers AI Navigator questions deterministically from the profile, skill gap, recommendations, and roadmap. No API key is needed. To enable the verified OpenAI path, copy `.env.example` to the ignored root `.env`, set `OPENAI_API_KEY` locally, `AI_PROVIDER=openai`, and `AI_FALLBACK_PROVIDER=template`. The backend loads `.env` at startup; process environment takes precedence. `NVIDIA_BASE_URL`, `NVIDIA_MODEL`, and `OPENAI_MODEL` are configurable. Restart the backend after changing `.env`.

The recommendation engine computes skill gaps, ranking, top-3, score breakdown, projected impact, and roadmap. The external model only explains this evidence packet. Provider output must pass a Pydantic JSON schema and checks for unknown IDs and unsupported numbers; invalid responses fall through to the next provider. `GET /api/ai/status` exposes safe configuration flags and the provider that answered the most recent Navigator request, with no secrets. The Navigator badge shows NVIDIA NIM or OpenAI only after a valid real response; otherwise it says Offline explanation. Activity completion is a demo simulation stored in API memory; full training remains in an external corporate LMS.

Check the selected provider with `.\.venv\Scripts\python.exe scripts\check_ai_providers.py`, then run five cases with `.\.venv\Scripts\python.exe scripts\eval_ai_providers.py`. Unselected providers are skipped; a selected provider without a key causes a nonzero exit. OpenAI passed live checks and a backend Navigator request on 23 September 2026. NVIDIA remains unverified without a key. See [AI integration status](docs/AI_INTEGRATION.md).

## Demo path

1. Employee `E0100` (Maria Ivanova) is preselected for the demo; clear the search to choose someone else. Enter Employee mode. The Product Manager Junior → Middle overview starts at 71.9% readiness and shows the key gap and first activity.
2. Open **Activities**, then **Подробнее и начать** on a recommendation. Review the dataset description, prerequisites, schedule, skill gains, forecast, and optional LMS link. Use **Записаться → Начать → Отметить выполненным**. The refreshed readiness, recommendations, roadmap, and activity history appear immediately. These status changes and skill gains live only in API memory. The repeatable `EV_036` can be enrolled again after completion.
3. Open **Roadmap** for up to three sequential steps and the full target skill map. Open **AI Navigator** for suggested questions or type your own. Answers include facts, reason, expected effect, limitation, next step, and source IDs.
4. Switch to HR overview from the sidebar for aggregate progress. To restore the initial demo state, restart the API.

Backend checks: `.\.venv\Scripts\python.exe -m pytest backend/tests tests -q --basetemp .pytest_local`. Golden-path smoke: `.\.venv\Scripts\python.exe scripts\demo_smoke_test.py` (isolated in-process API; E0100 goes from 71.9% to 81.2% on EV_026). Frontend checks: `npm --prefix frontend run typecheck` and `npm --prefix frontend run build`.

MVP behavior, final gaps, and API contracts are documented in [docs/MVP_SPEC.md](docs/MVP_SPEC.md), [docs/FINAL_GAP_ANALYSIS.md](docs/FINAL_GAP_ANALYSIS.md), and [contracts/api.md](contracts/api.md). For the defense use [demo script](docs/DEMO_SCRIPT.md), [jury Q&A](docs/JURY_QA.md), [scorecard](docs/JURY_SCORECARD.md), and [final checklist](docs/FINAL_CHECKLIST.md). Simulated activity actions are held in server memory and reset when the API restarts.
