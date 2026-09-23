# Career Quest MVP API

Base URL: `http://localhost:8000`; all paths begin with `/api`. JSON uses UTF-8 and `snake_case`; dates are ISO `YYYY-MM-DD`. No authentication in this demo. The Employee/HR entry choice changes the UI only. Shared wire models are in [types.md](types.md).

The backend loads dataset files relative to the repository, independent of launch directory. Use the dataset `as_of_date` (`2026-10-01` in the supplied data) for dates and session filtering, never the computer clock. GET requests have no body. All responses are `application/json`.

| Method and path | Request | 200 response | Other responses |
| --- | --- | --- | --- |
| `GET /api/health` | None | `HealthResponse` | `503 data_unavailable` if data cannot load |
| `GET /api/employees` | None | `EmployeeListResponse`, all employees sorted by full name then ID | `503 data_unavailable` |
| `GET /api/employees/{employee_id}` | Path ID | `EmployeeProfileResponse` | `404 not_found` |
| `GET /api/employees/{employee_id}/skill-gap` | Path ID | `SkillGapResponse` | `404 not_found` |
| `GET /api/employees/{employee_id}/recommendations` | Path ID | `RecommendationsResponse` with 0–3 items sorted by score descending, then event ID | `404 not_found` |
| `GET /api/employees/{employee_id}/roadmap` | Path ID | `RoadmapResponse` | `404 not_found` |
| `GET /api/employees/{employee_id}/activities/{event_id}` | Path IDs | `ActivityDetailsResponse` | `404 not_found` |
| `GET /api/employees/{employee_id}/activity-history` | Path ID | `ActivityHistoryResponse`, dataset records plus demo statuses | `404 not_found` |
| `POST /api/employees/{employee_id}/activities/{event_id}/actions/enroll` | Path IDs | `ActivityActionResponse`, status `enrolled` | `404 not_found`, `409 already_completed`, `422 invalid_activity` |
| `POST /api/employees/{employee_id}/activities/{event_id}/actions/start` | Path IDs | `ActivityActionResponse`, status `in_progress` | `404 not_found`, `409 enrollment_required` / `already_completed`, `422 invalid_activity` |
| `POST /api/employees/{employee_id}/activities/{event_id}/complete` | Path IDs; no body or `{}` | `CompletionResponse` | `404 not_found`, `409 already_completed`, `422 invalid_activity` |
| `POST /api/employees/{employee_id}/navigator/ask` | JSON `{question, intent?, event_id?, weekly_hours?}` | `NavigatorResponse` | `404 not_found`, `422 validation_error` |
| `GET /api/hr/overview` | None | `HROverviewResponse` | `503 data_unavailable` |

## Endpoint behavior

`GET /api/employees/{employee_id}` returns dataset profile fields plus effective skill levels after in-memory simulation. Its `target` follows the target-resolution rule in [MVP_SPEC.md](../docs/MVP_SPEC.md).

`skill-gap` includes every target-required skill, including met skills. Without a target it returns `status: "no_target"`, null progress, zero totals, and an empty `skills` array. A fully met target returns `status: "ready"`. Missing skill levels count as zero.

`recommendations` returns an empty array when no target, no remaining gap, or no eligible event exists. Each recommendation carries event fields, score and five weighted components, matched skill gains, projected progress, and a template explanation. No LLM chooses or orders activities.

`roadmap` computes up to three **sequential** distinct recommendations against a copy of skills, recalculating after each virtual completion. It never mutates session state. Status is `in_progress`, `ready`, `no_target`, or `no_activities`; the last means a positive gap with no eligible recommendation. Null progress is reserved for `no_target`.

`complete` applies event gains to effective in-memory skills and returns the refreshed gap, recommendations, and roadmap. Subsequent GET calls see the same state until backend restart. The JSON/CSV source is unchanged. The action simulates completion immediately, even when the next real session is in the future. A historically or session-completed nonrepeatable event returns `409`; `EV_036` is repeatable. Mandatory, role/grade-ineligible, prerequisite-blocked, or session-unavailable activities return `422`. An eligible event may complete with no effective gain when capped at `max_level`, but recommendations omit activities that close no target gap.

`activities/{event_id}` returns the source description, format, duration, upcoming sessions, prerequisites with current levels, developed skills, eligibility, current demo status, and any matching recommendation. `external_url` and `provider_url` are nullable and accepted only when the dataset contains valid HTTP(S) URLs. No LMS URL is synthesized. `actions/enroll` and `actions/start` update in-memory status; start requires enrollment. The legacy direct `complete` action remains supported for existing clients.

`activity-history` returns all historical event rows for that employee, sorted newest first, with the source event title. Current demo statuses appear first with `source: "demo"` and `date: null` because the dataset does not provide a date for a simulated action.

`navigator/ask` accepts an optional intent (`why_course`, `blockers`, `first_skill`, `after_activity`, `faster_route`, `four_hours`, or `general`). It derives facts and projected effects from the same engine functions as the dashboard without mutating skills. A stated weekly time budget such as “2 часа” is parsed from the question unless `weekly_hours` is supplied. `evidence_ids` reference actual employee, skill, and event IDs. The default template works without credentials. Optional OpenAI/NVIDIA adapters choose between brief and contextual summaries assembled from computed text; model output cannot introduce facts. Provider failures fall back to the template answer. The optional network call runs after releasing dataset state lock.

`hr/overview` aggregates current effective state: employee and goal counts, ready/no-target counts, average target progress, grade counts, and department summaries. Exclude null progress from averages.

## Error shape

`{ "error": { "code": "not_found", "message": "Employee E9999 not found" } }`. Other codes: `already_completed`, `enrollment_required`, `invalid_activity`, `data_unavailable`, `validation_error`. Frontend displays `message` and offers retry where applicable.

