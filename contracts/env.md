# Environment Contract

Status: implemented

Copy `.env.example` to `.env` only when overriding the local defaults.

| Variable | Service | Required | Default / purpose |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | backend | production | Local demo key is provided by Compose |
| `DJANGO_DEBUG` | backend | no | `1`; set `0` outside local development |
| `DJANGO_ALLOWED_HOSTS` | backend | no | `*` |
| `CORS_ALLOWED_ORIGINS` | backend | no | Local Vite origins |
| `POSTGRES_DB` | backend/db | no | `career_quest` |
| `POSTGRES_USER` | backend/db | no | `career_quest` |
| `POSTGRES_PASSWORD` | backend/db | no | `career_quest` |
| `POSTGRES_HOST` | backend | Compose | `db`; omit to use SQLite locally |
| `POSTGRES_PORT` | backend | no | `5432` |
| `CAREER_DATASET_PATH` | backend | no | Repository `datasets/career_quest` directory |
| `CAREER_SNAPSHOT_DATE` | backend | no | `2026-10-01` |
| `VITE_API_BASE_URL` | frontend | no | `http://localhost:8000/api/v1` |
