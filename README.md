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

The default `AI_PROVIDER=template` generates deterministic explanations and needs no API key. `.env.example` lists optional provider names and key variables. The current OpenAI and NVIDIA adapters also use template explanations; they do not call external services. The backend reads process environment variables and does not load a `.env` file automatically. To select a provider for one PowerShell session, set the variable before starting the API, for example `$env:AI_PROVIDER = 'template'`.

MVP behavior and API contracts are documented in [docs/MVP_SPEC.md](docs/MVP_SPEC.md) and [contracts/api.md](contracts/api.md). Simulated activity completions are held in server memory and reset when the API restarts.
