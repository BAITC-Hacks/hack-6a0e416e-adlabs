# Career Quest

Career Quest is a working hackathon MVP for personalized employee development. It imports the supplied employee, skill, role-profile, learning-event, and activity-history dataset; calculates effective skills and weighted role readiness; recommends explainable quest chains; and exposes separate employee and aggregate HR experiences.

## Run in one command

Prerequisite: Docker with Compose.

```bash
docker compose up --build
```

Open:

- Frontend: <http://localhost:5173>
- API health: <http://localhost:8000/api/v1/health/>

The backend applies migrations and idempotently imports the dataset on every container start. PostgreSQL data is kept in the `career_quest_db` volume.

## Demo flow

1. Select `E0001` on the first screen.
2. Review readiness, critical gaps, and the recommended quest.
3. Open **Quests**. `EV_006` initially shows an unlock chain through `EV_005`.
4. Start and complete `EV_005`; readiness, effective skills, XP, rank progress, and recommendations are recalculated.
5. Ask the AI Coach why the next quest is recommended, then switch language between RU, EN, and KZ.
6. Switch the top-right role control to **HR** to inspect aggregate gaps and participation without an employee ranking.

See [contracts/demo-flow.md](contracts/demo-flow.md) for the presentation script.

## Architecture

- `backend/`: Django 5 + Django REST Framework; PostgreSQL in Compose and SQLite for lightweight local development/tests.
- `frontend/`: React 19 + TypeScript + Vite; responsive employee and HR interfaces, served by Nginx in Compose.
- `datasets/career_quest/`: source JSON/CSV dataset imported by `import_career_dataset`.
- `contracts/`: API, environment, and demo contracts.

The deterministic Career Engine is the source of truth for effective skills, skill gaps, readiness, recommendations, quest chains, XP, ranks, and achievements. The coach is a controlled explanation layer over the same data, with RU/EN/KZ deterministic responses and no invented profile facts.

## Local development

Backend:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
.venv/bin/python backend/manage.py migrate
.venv/bin/python backend/manage.py import_career_dataset
.venv/bin/python backend/manage.py runserver 0.0.0.0:8000
```

Frontend, in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

## Verification

```bash
.venv/bin/python backend/manage.py test career
cd frontend && npm run lint && npm test && npm run build
```

GitHub Actions repeats both test suites and runs a clean Compose smoke test for every push and pull request.

## Team workflow

- Team rules: `AGENTS.md`
- Workflow: `TEAM_WORKFLOW.md`
- Hourly commit helper: `scripts/team-commit`
- Task router: `scripts/route-task`
