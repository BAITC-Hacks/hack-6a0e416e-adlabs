# Career Quest MVP specification

## Scope and architecture

This hackathon build is a React/TypeScript/Vite client, a FastAPI JSON server, and a deterministic Python recommendation engine. The server loads four repository datasets at startup: `skills.json` (skill catalog and 32 role/grade profiles), `employees.json` (200 baseline employees), `events.json` (40 events), and `activity_history.csv` (2,743 records). Do not hard-code those counts: evaluation supplies additional profiles and history in the same format. The server resolves file paths from its module/repository location, not the process working directory. The snapshot date comes from dataset metadata (`2026-10-01` in this release). The browser uses the eight endpoints in [api.md](../contracts/api.md) and the models in [types.md](../contracts/types.md).

The demo entry screen selects a dataset employee and Employee or HR view. There is no registration or authorization. Effective skills and simulated completions are held in server memory by employee ID. Restarting the server resets them; simultaneous demo clients share them. Historical completed events after `last_review_date` are **not** replayed into skills because the dataset says assessed skill levels already reflect the last review and newer completions have not been assessed. History is used for eligibility and completion-rate evidence. A completion made through the API updates effective skills immediately for the demo.

The engine takes plain dataset records and effective skills, returns pure gap/recommendation/roadmap calculations, and does not call an LLM. `TemplateAIProvider` formats a transparent explanation. AI Navigator answers questions from the same calculations and returns evidence IDs. Optional OpenAI/NVIDIA adapters choose between precomputed brief and contextual summaries; they never choose or reorder recommendations or add facts. The UI shows loading, error, and empty states, including no career target and no eligible activities. Overview, Roadmap, Activities, and AI Navigator separate the employee flow.

## Target and skill gap

Grade order is `Junior → Middle → Senior → Lead`. Resolve target as follows:

1. A valid explicit `career_goal` selects exactly `(target_role, target_grade)` with `source = career_goal`, including cross-role goals.
2. Otherwise select the next grade of the employee's current role with `source = next_grade`.
3. A Lead with no explicit goal has `target = null` and `status = no_target`. Do not invent a grade above Lead or silently use the current grade.

An explicit goal must match a `role_profiles` entry; invalid dataset references fail validation. `next grade` in the UI may be shown separately as the ordinary ladder step, but all gaps and recommendations use the resolved target. An explicit goal equal to the current role and grade is permitted and evaluated against that profile.

For each required target skill `s`, `current_s = effective_skills.get(s, 0)`, `required_s = target.required_skills[s]`, `gap_s = max(0, required_s - current_s)`, and `met_s = min(current_s, required_s)`. Then:

```text
total_required_points = Σ required_s
total_met_points      = Σ met_s
total_gap_points      = Σ gap_s
progress_pct          = 100 × total_met_points / total_required_points
critical_gap_points   = Σ gap_s where s is in target.critical_skills
```

All sums range over target-required skills. A target with zero total requirements is 100% ready. `critical_skills_met` counts required critical skills whose gap is zero; `critical_skills_total` counts critical skills. `ready` means `total_gap_points = 0`, including all critical skills. Sort gap items critical first, then gap descending, then ID. Current levels above requirements contribute no extra credit. Public percentages are rounded to one decimal, with internal calculations left unrounded.

## Event eligibility and score

An event is eligible when all conditions hold:

- It is voluntary (`mandatory = false`). Compliance assignments never appear as recommendations.
- Its `target_roles` and `target_grades` include **either** the employee's current `(role, grade)` or resolved target `(role, grade)`. The latter enables cross-role goals.
- Each `prerequisites` skill is at or above the event's minimum in effective skills.
- It has not been completed historically or in this process, except `EV_036`, the dataset's documented repeatable Public Speaking Club. A dropped, declined, no-show, overdue, or in-progress history record does not permanently exclude a voluntary event.
- A scheduled event has at least one `upcoming_sessions` date on/after the snapshot date. Its `next_session_date` is the earliest such date. `self_paced` has `next_session_date = null` and is always available.
- At least one developed skill closes a positive gap in the resolved target. This last condition is for **recommendations**; the completion API may simulate an otherwise eligible event even if its target impact is zero.

For each developed skill, `projected_level = min(5, max_level, current_level + gain)`, `actual_gain = max(0, projected_level - current_level)`, and `gap_closed = min(actual_gain, gap_s)`; a skill absent from target requirements has `gap_closed = 0`. These caps matter for projected impact and ranking. The five component scores, expressed as points, are:

```text
critical_skill_coverage = 45 × critical_gap_closed / critical_gap_points
total_gap_coverage      = 25 × total_gap_closed / total_gap_points
career_goal_alignment   = 15 × I[event targets resolved target role AND grade]
completion_likelihood   = 10 × (event_completed + 1) / (event_terminal + 2)
time_efficiency         =  5 × min(1, 2 / duration_hours)
score                   = sum of the five components
```

`event_terminal` counts event history rows with `completed`, `dropped`, `no_show`, `declined`, or `overdue`; `event_completed` counts `completed`. `in_progress` is excluded. Laplace smoothing makes an event with no terminal records 50%, rather than an invented certainty. If `critical_gap_points = 0`, give every candidate the same full 45 points; this constant does not change ranking. `total_gap_points = 0` yields no recommendations. Duration must be positive; invalid source data fails validation. All components and final score are returned as weighted points (0–45/25/15/10/5 and 0–100), rounded only at serialization. Stable tie break: `event_id` ascending. This preserves the requested 45/25/15/10/5 weighting while grounding likelihood in actual history.

The explanation names the target, relevant skill gaps, expected gain, and at least one reason from the score breakdown. It must not claim an event guarantees promotion. `projected_impact` recomputes the gap on a copied skill map, so progress delta is in percentage points and may be zero only for a direct completion outside the recommendation list.

## Roadmap and completion

The roadmap starts with effective skills and repeatedly takes the highest eligible recommendation, applies its capped gains **to a copy**, removes that event from this roadmap, and recomputes up to three steps. It stops when the target is ready or no activity can close a remaining gap. A roadmap GET has no side effects. When there is no target it returns `no_target` with null progress; when already ready it returns `ready` with empty steps; when a positive gap has no activities it returns `no_activities` with empty steps. After partial steps, status is `ready` if the target is met, `no_activities` if no further eligible activity exists, otherwise `in_progress` after the three-step limit.

The completion POST validates the employee/event, repeatability, audience, prerequisites, and session availability, then adds capped gains to the in-memory effective skill map. It records the session completion so subsequent calls cannot repeat a nonrepeatable event. Repeatable `EV_036` can be completed more than once but never exceed its `max_level`. The response contains applied gains and refreshed gap/recommendations/roadmap. No source file is modified; this is not evidence of actual attendance or assessment.

## Key edge cases

- Missing explicit goal: use next current-role grade; for a Lead return `no_target` and empty recommendations/roadmap.
- Missing skill key: level zero. Overqualified skill: no negative gap or extra progress.
- Explicit cross-role goal: use that role's profile and allow activities aimed at either current or target role/grade.
- Fully met target: `ready`, progress 100, no recommendations.
- No eligible impact: empty top-3 and `no_activities`, not fabricated events.
- Fewer than three matches: return only the available items.
- Historical completion after last assessment: blocks a nonrepeatable recommendation but does not silently modify assessed skills.
- `EV_036` may recur; all other historical/session completions block another completion.
- Scheduled event without a future session: not eligible; `self_paced` needs no session.
- Simulated completion at a cap may have zero gain; do not let it reduce levels or progress.
- Average HR progress excludes `no_target` employees; zero denominators produce `null` rather than NaN.
