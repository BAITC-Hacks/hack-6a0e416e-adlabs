"""Pure, dataset-driven Career Quest calculations.

The functions accept plain JSON/CSV records and never modify their inputs. The
backend owns the in-memory session state and passes effective skill levels here.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

GRADES = ("Junior", "Middle", "Senior", "Lead")
REPEATABLE_EVENT_ID = "EV_036"
TERMINAL_STATUSES = frozenset({"completed", "dropped", "no_show", "declined", "overdue"})


def _profile(target: Mapping[str, Any], role_profiles: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    for profile in role_profiles:
        if profile["role"] == target["role"] and profile["grade"] == target["grade"]:
            return profile
    raise ValueError(f"Unknown role profile: {target['role']} / {target['grade']}")


def resolve_target(
    employee: Mapping[str, Any], role_profiles: Sequence[Mapping[str, Any]]
) -> dict[str, str] | None:
    """Resolve an explicit career goal or the next grade in the current role."""
    goal = employee.get("career_goal")
    if goal is not None:
        target = {"role": goal["target_role"], "grade": goal["target_grade"], "source": "career_goal"}
    else:
        grade = employee["grade"]
        if grade not in GRADES:
            raise ValueError(f"Unknown grade: {grade}")
        index = GRADES.index(grade) + 1
        if index >= len(GRADES):
            return None
        target = {"role": employee["role"], "grade": GRADES[index], "source": "next_grade"}
    _profile(target, role_profiles)
    return target


def calculate_skill_gap(
    employee: Mapping[str, Any],
    skills: Mapping[str, int],
    catalog: Sequence[Mapping[str, Any]],
    role_profiles: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a complete SkillGapResponse, including requirements already met."""
    target = resolve_target(employee, role_profiles)
    result: dict[str, Any] = {
        "employee_id": employee["employee_id"],
        "target": target,
        "status": "no_target" if target is None else "in_progress",
        "progress_pct": None,
        "total_required_points": 0,
        "total_met_points": 0,
        "total_gap_points": 0,
        "critical_gap_points": 0,
        "critical_skills_met": 0,
        "critical_skills_total": 0,
        "skills": [],
    }
    if target is None:
        return result

    profile = _profile(target, role_profiles)
    details = {skill["skill_id"]: skill for skill in catalog}
    critical = set(profile["critical_skills"])
    items = []
    for skill_id, required in profile["required_skills"].items():
        current = skills.get(skill_id, 0)
        gap = max(0, required - current)
        item = {
            "skill_id": skill_id,
            "name": details[skill_id]["name"],
            "type": details[skill_id]["type"],
            "category": details[skill_id]["category"],
            "current_level": current,
            "required_level": required,
            "gap": gap,
            "critical": skill_id in critical,
        }
        items.append(item)
        result["total_required_points"] += required
        result["total_met_points"] += min(current, required)
        result["total_gap_points"] += gap
        if skill_id in critical:
            result["critical_gap_points"] += gap
            result["critical_skills_met"] += int(gap == 0)
    items.sort(key=lambda item: (not item["critical"], -item["gap"], item["skill_id"]))
    result["skills"] = items
    result["critical_skills_total"] = len(critical)
    required_points = result["total_required_points"]
    result["progress_pct"] = round(100 * result["total_met_points"] / required_points, 1) if required_points else 100.0
    result["status"] = "ready" if result["total_gap_points"] == 0 else "in_progress"
    return result


def _next_session(event: Mapping[str, Any], as_of_date: str) -> str | None:
    if event["format"] == "self_paced":
        return None
    future = (day for day in event.get("upcoming_sessions", ()) if day >= as_of_date)
    return min(future, default=None)


def event_is_eligible(
    event: Mapping[str, Any],
    employee: Mapping[str, Any],
    skills: Mapping[str, int],
    target: Mapping[str, Any] | None,
    history: Sequence[Mapping[str, Any]],
    as_of_date: str,
    completed_event_ids: Iterable[str] | None = None,
) -> bool:
    """Check completion eligibility; recommendation impact is checked separately."""
    if event["mandatory"]:
        return False
    audience = ((employee["role"], employee["grade"]),)
    if target is not None:
        audience += ((target["role"], target["grade"]),)
    if not any(role in event["target_roles"] and grade in event["target_grades"] for role, grade in audience):
        return False
    if any(skills.get(skill_id, 0) < minimum for skill_id, minimum in event["prerequisites"].items()):
        return False
    if event["event_id"] != REPEATABLE_EVENT_ID:
        if event["event_id"] in (completed_event_ids or ()):
            return False
        if any(
            row["employee_id"] == employee["employee_id"]
            and row["event_id"] == event["event_id"]
            and row["status"] == "completed"
            for row in history
        ):
            return False
    return event["format"] == "self_paced" or _next_session(event, as_of_date) is not None


def apply_event_gains(event: Mapping[str, Any], skills: Mapping[str, int]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Apply capped gains to a copy, returning the copy and all gain records."""
    updated = dict(skills)
    applied = []
    seen: set[str] = set()
    for developed in event["develops_skills"]:
        skill_id = developed["skill_id"]
        if skill_id in seen:
            raise ValueError(f"Duplicate developed skill {skill_id} in {event['event_id']}")
        seen.add(skill_id)
        before = updated.get(skill_id, 0)
        after = max(before, min(5, developed["max_level"], before + developed["gain"]))
        updated[skill_id] = after
        applied.append({"skill_id": skill_id, "before_level": before, "after_level": after, "gain": after - before})
    return updated, applied


def _history_counts(history: Sequence[Mapping[str, Any]]) -> dict[str, tuple[int, int]]:
    completed: Counter[str] = Counter()
    terminal: Counter[str] = Counter()
    for row in history:
        status = row["status"]
        event_id = row["event_id"]
        if status in TERMINAL_STATUSES:
            terminal[event_id] += 1
            if status == "completed":
                completed[event_id] += 1
    return {event_id: (completed[event_id], count) for event_id, count in terminal.items()}


def _recommendations(
    employee: Mapping[str, Any],
    skills: Mapping[str, int],
    catalog: Sequence[Mapping[str, Any]],
    role_profiles: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    history: Sequence[Mapping[str, Any]],
    as_of_date: str,
    completed_event_ids: Iterable[str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    gap = calculate_skill_gap(employee, skills, catalog, role_profiles)
    target = gap["target"]
    if target is None or gap["total_gap_points"] == 0 or limit <= 0:
        return []
    gaps = {item["skill_id"]: item for item in gap["skills"]}
    names = {item["skill_id"]: item["name"] for item in catalog}
    counts = _history_counts(history)
    candidates: list[tuple[float, dict[str, Any]]] = []
    for event in events:
        if not event_is_eligible(event, employee, skills, target, history, as_of_date, completed_event_ids):
            continue
        if event["duration_hours"] <= 0:
            raise ValueError(f"Nonpositive duration for {event['event_id']}")
        projected_skills, _ = apply_event_gains(event, skills)
        matched = []
        critical_closed = total_closed = 0
        for developed in event["develops_skills"]:
            skill_id = developed["skill_id"]
            item = gaps.get(skill_id)
            if item is None:
                continue
            current = skills.get(skill_id, 0)
            projected = projected_skills[skill_id]
            closed = min(max(0, projected - current), item["gap"])
            if closed <= 0:
                continue
            matched.append({
                "skill_id": skill_id,
                "name": names[skill_id],
                "current_level": current,
                "required_level": item["required_level"],
                "projected_level": projected,
                "gap_closed": closed,
                "critical": item["critical"],
            })
            total_closed += closed
            if item["critical"]:
                critical_closed += closed
        if total_closed == 0:
            continue
        matched.sort(key=lambda item: (not item["critical"], -item["gap_closed"], item["skill_id"]))
        completed, terminal = counts.get(event["event_id"], (0, 0))
        aligned = target["role"] in event["target_roles"] and target["grade"] in event["target_grades"]
        raw_breakdown = {
            "critical_skill_coverage": 45 * critical_closed / gap["critical_gap_points"] if gap["critical_gap_points"] else 45.0,
            "total_gap_coverage": 25 * total_closed / gap["total_gap_points"],
            "career_goal_alignment": 15.0 if aligned else 0.0,
            "completion_likelihood": 10 * (completed + 1) / (terminal + 2),
            "time_efficiency": 5 * min(1, 2 / event["duration_hours"]),
        }
        raw_score = sum(raw_breakdown.values())
        after_gap = calculate_skill_gap(employee, projected_skills, catalog, role_profiles)
        before_progress = 100 * gap["total_met_points"] / gap["total_required_points"] if gap["total_required_points"] else 100.0
        after_progress = 100 * after_gap["total_met_points"] / after_gap["total_required_points"] if after_gap["total_required_points"] else 100.0
        skill_text = ", ".join(f"{item['name']} (+{item['gap_closed']})" for item in matched[:3])
        reason = "critical skill coverage" if critical_closed else "overall gap coverage"
        recommendation = {
            "event_id": event["event_id"],
            "title": event["title"],
            "description": event["description"],
            "type": event["type"],
            "format": event["format"],
            "duration_hours": event["duration_hours"],
            "next_session_date": _next_session(event, as_of_date),
            "score": round(raw_score, 1),
            "score_breakdown": {key: round(value, 1) for key, value in raw_breakdown.items()},
            "matched_skill_gains": matched,
            "projected_impact": {
                "progress_before_pct": round(before_progress, 1),
                "progress_after_pct": round(after_progress, 1),
                "progress_delta_pct": round(after_progress - before_progress, 1),
                "total_gap_points_before": gap["total_gap_points"],
                "total_gap_points_after": after_gap["total_gap_points"],
                "critical_gap_points_after": after_gap["critical_gap_points"],
            },
            "explanation": (
                f"For your {target['role']} {target['grade']} target, {event['title']} "
                f"addresses the gaps in {skill_text}. It could raise target progress "
                f"by {round(after_progress - before_progress, 1):.1f} percentage points. "
                f"The score reflects {reason} ({raw_breakdown['critical_skill_coverage' if critical_closed else 'total_gap_coverage']:.1f} points)."
            ),
        }
        candidates.append((raw_score, recommendation))
    candidates.sort(key=lambda pair: (-pair[0], pair[1]["event_id"]))
    return [recommendation for _, recommendation in candidates[:limit]]


def recommend_activities(
    employee: Mapping[str, Any],
    skills: Mapping[str, int],
    catalog: Sequence[Mapping[str, Any]],
    role_profiles: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    history: Sequence[Mapping[str, Any]],
    as_of_date: str,
    completed_event_ids: Iterable[str] | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Return at most ``limit`` ranked recommendations without mutating inputs."""
    return _recommendations(employee, skills, catalog, role_profiles, events, history, as_of_date, completed_event_ids, limit)


def build_roadmap(
    employee: Mapping[str, Any],
    skills: Mapping[str, int],
    catalog: Sequence[Mapping[str, Any]],
    role_profiles: Sequence[Mapping[str, Any]],
    events: Sequence[Mapping[str, Any]],
    history: Sequence[Mapping[str, Any]],
    as_of_date: str,
    completed_event_ids: Iterable[str] | None = None,
    limit: int = 3,
) -> dict[str, Any]:
    """Greedily recompute up to three distinct steps against a copied skill map."""
    initial = calculate_skill_gap(employee, skills, catalog, role_profiles)
    result = {
        "employee_id": employee["employee_id"],
        "target": initial["target"],
        "status": initial["status"],
        "starting_progress_pct": initial["progress_pct"],
        "ending_progress_pct": initial["progress_pct"],
        "steps": [],
    }
    if initial["target"] is None or initial["status"] == "ready":
        return result
    virtual_skills = dict(skills)
    used = set(completed_event_ids or ())
    event_by_id = {event["event_id"]: event for event in events}
    for order in range(1, min(limit, 3) + 1):
        remaining_events = [event for event in events if event["event_id"] not in used]
        recommendations = _recommendations(employee, virtual_skills, catalog, role_profiles, remaining_events, history, as_of_date, used, 1)
        if not recommendations:
            result["status"] = "no_activities"
            break
        recommendation = recommendations[0]
        result["steps"].append({
            "order": order,
            "recommendation": recommendation,
            "progress_before_pct": recommendation["projected_impact"]["progress_before_pct"],
            "progress_after_pct": recommendation["projected_impact"]["progress_after_pct"],
        })
        used.add(recommendation["event_id"])
        virtual_skills, _ = apply_event_gains(event_by_id[recommendation["event_id"]], virtual_skills)
        current_gap = calculate_skill_gap(employee, virtual_skills, catalog, role_profiles)
        result["ending_progress_pct"] = current_gap["progress_pct"]
        if current_gap["status"] == "ready":
            result["status"] = "ready"
            break
    else:
        remaining_events = [event for event in events if event["event_id"] not in used]
        remaining = _recommendations(employee, virtual_skills, catalog, role_profiles, remaining_events, history, as_of_date, used, 1)
        result["status"] = "in_progress" if remaining else "no_activities"
    return result
