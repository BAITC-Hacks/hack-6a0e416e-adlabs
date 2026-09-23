# API Contract

Status: implemented

## Base URL

```text
http://localhost:8000/api/v1
```

All responses are JSON. Employee-scoped requests send:

```text
X-Demo-Role: employee
X-Employee-ID: E0001
```

The aggregate HR endpoint requires `X-Demo-Role: hr`. Employee-scoped endpoints require an exact `X-Employee-ID`; HR cannot open them or the employee directory. Errors use:

```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Human-readable message",
    "details": {}
  }
}
```

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health/` | Service health, snapshot date, and source counts |
| `GET` | `/employees/?q=&limit=` | Demo employee selector and search |
| `GET` | `/employees/{employee_id}/` | Employee profile |
| `GET` | `/employees/{employee_id}/dashboard/` | Goal, readiness, route, gaps, next quest, and progress |
| `GET` | `/employees/{employee_id}/skills/` | Baseline/effective skill levels and target gaps |
| `GET` | `/employees/{employee_id}/career/` | Current/target positions, route, and readiness |
| `POST` | `/employees/{employee_id}/career-goal/` | Update target role and grade |
| `GET` | `/employees/{employee_id}/recommendations/` | One to three explainable ranked recommendations |
| `GET` | `/employees/{employee_id}/quests/` | Recommended, active, and completed quest groups |
| `GET` | `/role-profiles/` | Valid target role/grade combinations |
| `POST` | `/quests/{event_id}/start/` | Atomically start an eligible quest |
| `POST` | `/quests/{event_id}/complete/` | Atomically complete a quest and recalculate progress |
| `POST` | `/ai/chat/` | Controlled career-coach response in RU/EN/KZ |
| `GET` | `/hr/overview/` | Aggregate gaps, participation, and employees missing a goal/step |

## Mutations

Update career goal:

```json
{
  "target_role": "Data Analyst",
  "target_grade": "Middle"
}
```

Start or complete a quest:

```json
{
  "employee_id": "E0001"
}
```

Completion requires an active quest (or a source `in_progress` activity). Repeated start/complete requests are idempotent. Mandatory events, events outside the current goal, completed events, and unmet prerequisites are rejected. `EV_036` is repeatable: starting it after completion opens a new cycle, while retrying the same completion does not duplicate history or XP.

Coach request:

```json
{
  "employee_id": "E0001",
  "question": "Почему рекомендован этот квест?",
  "language": "ru"
}
```
