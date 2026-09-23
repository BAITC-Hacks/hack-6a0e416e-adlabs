from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import Any, Iterable

from django.db.models import Sum

from career.models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, Skill


GRADE_ORDER = ["Junior", "Middle", "Senior", "Lead"]
RANKS = [
    (0, "Explorer"),
    (1_000, "Practitioner"),
    (3_000, "Specialist"),
    (6_000, "Expert"),
    (10_000, "Master"),
]


def serialize_employee(employee: Employee) -> dict[str, Any]:
    return {
        "employee_id": employee.external_id,
        "full_name": employee.full_name,
        "department": employee.department,
        "role": employee.role,
        "grade": employee.grade,
        "manager_id": employee.manager_id,
        "hire_date": employee.hire_date.isoformat(),
        "tenure_months": employee.tenure_months,
        "work_format": employee.work_format,
        "preferred_language": employee.preferred_language,
        "career_goal": employee.career_goal,
        "last_review_date": employee.last_review_date.isoformat(),
    }


def serialize_event(event: LearningEvent) -> dict[str, Any]:
    return {
        "event_id": event.external_id,
        "title": event.title,
        "description": event.description,
        "type": event.type,
        "format": event.format,
        "duration_hours": float(event.duration_hours),
        "mandatory": event.mandatory,
        "develops_skills": event.develops_skills,
        "prerequisites": event.prerequisites,
        "upcoming_sessions": event.upcoming_sessions,
    }


def effective_skills(employee: Employee) -> dict[str, int]:
    values = {skill_id: int(level) for skill_id, level in employee.skills.items()}
    completions = (
        employee.activities.filter(status="completed", date__gt=employee.last_review_date)
        .select_related("event")
        .order_by("date", "record_id")
    )
    for completion in completions:
        for gain in completion.event.develops_skills:
            skill_id = gain["skill_id"]
            current = values.get(skill_id, 0)
            values[skill_id] = min(current + int(gain["gain"]), int(gain["max_level"]))
    return values


def target_profile(employee: Employee) -> RoleProfile | None:
    if not employee.career_goal:
        return None
    return RoleProfile.objects.filter(
        role=employee.career_goal.get("target_role"),
        grade=employee.career_goal.get("target_grade"),
    ).first()


def readiness_for_values(profile: RoleProfile | None, values: dict[str, int]) -> int:
    if profile is None:
        return 0
    weighted_score = 0.0
    total_weight = 0.0
    critical = set(profile.critical_skills)
    for skill_id, required in profile.required_skills.items():
        required_level = int(required)
        if required_level <= 0:
            continue
        weight = 2.0 if skill_id in critical else 1.0
        weighted_score += min(values.get(skill_id, 0) / required_level, 1.0) * weight
        total_weight += weight
    return round(weighted_score / total_weight * 100) if total_weight else 0


def skill_gap(employee: Employee, values: dict[str, int] | None = None) -> list[dict[str, Any]]:
    profile = target_profile(employee)
    if profile is None:
        return []
    values = values or effective_skills(employee)
    catalog = {skill.external_id: skill for skill in Skill.objects.all()}
    critical = set(profile.critical_skills)
    result = []
    for skill_id, required in profile.required_skills.items():
        current = int(values.get(skill_id, 0))
        required_level = int(required)
        item = catalog.get(skill_id)
        result.append(
            {
                "skill_id": skill_id,
                "name": item.name if item else skill_id,
                "category": item.category if item else "other",
                "current": current,
                "required": required_level,
                "gap": max(required_level - current, 0),
                "critical": skill_id in critical,
            }
        )
    return sorted(result, key=lambda item: (not item["critical"], -item["gap"], item["name"]))


def readiness(employee: Employee, values: dict[str, int] | None = None) -> int:
    return readiness_for_values(target_profile(employee), values or effective_skills(employee))


def _eligible(event: LearningEvent, goal: dict[str, str]) -> bool:
    return goal["target_role"] in event.target_roles and goal["target_grade"] in event.target_grades


def _unmet_prerequisites(event: LearningEvent, values: dict[str, int]) -> dict[str, int]:
    return {
        skill_id: int(required)
        for skill_id, required in event.prerequisites.items()
        if values.get(skill_id, 0) < int(required)
    }


def _unlock_chain(
    target: LearningEvent,
    values: dict[str, int],
    goal: dict[str, str],
    events: Iterable[LearningEvent],
) -> list[dict[str, Any]]:
    chain: list[LearningEvent] = []
    selected_ids: set[str] = set()
    for skill_id, required in _unmet_prerequisites(target, values).items():
        candidates = []
        for event in events:
            if event.mandatory or event.external_id == target.external_id or not _eligible(event, goal):
                continue
            gain = next((item for item in event.develops_skills if item["skill_id"] == skill_id), None)
            if not gain or int(gain["max_level"]) < required:
                continue
            unmet_count = len(_unmet_prerequisites(event, values))
            candidates.append((unmet_count, float(event.duration_hours), event.external_id, event))
        if candidates:
            unlocker = min(candidates)[-1]
            if unlocker.external_id not in selected_ids:
                selected_ids.add(unlocker.external_id)
                chain.append(unlocker)
        if len(chain) >= 2:
            break
    chain.append(target)
    return [serialize_event(event) for event in chain[:3]]


def _projected_values(values: dict[str, int], event: LearningEvent) -> dict[str, int]:
    projected = deepcopy(values)
    for gain in event.develops_skills:
        skill_id = gain["skill_id"]
        projected[skill_id] = min(
            projected.get(skill_id, 0) + int(gain["gain"]), int(gain["max_level"])
        )
    return projected


def recommendations(
    employee: Employee,
    *,
    limit: int = 3,
    event_pool: list[LearningEvent] | None = None,
) -> list[dict[str, Any]]:
    goal = employee.career_goal
    profile = target_profile(employee)
    if not goal or profile is None:
        return []

    values = effective_skills(employee)
    gaps = skill_gap(employee, values)
    open_gaps = {item["skill_id"]: item for item in gaps if item["gap"] > 0}
    critical_ids = {item["skill_id"] for item in gaps if item["critical"] and item["gap"] > 0}
    current_readiness = readiness_for_values(profile, values)
    histories = list(employee.activities.select_related("event"))
    completed_ids = {item.event_id for item in histories if item.status == "completed"}
    active_ids = {item.event_id for item in histories if item.status == "in_progress"}
    active_ids.update(employee.quests.filter(state=EmployeeQuest.State.ACTIVE).values_list("event_id", flat=True))

    events = event_pool if event_pool is not None else list(LearningEvent.objects.all())
    ranked: list[tuple[float, float, str, dict[str, Any]]] = []
    for event in events:
        if event.mandatory or not _eligible(event, goal):
            continue
        if event.external_id in active_ids:
            continue
        if event.external_id in completed_ids and event.external_id != "EV_036":
            continue

        relevant = [gain for gain in event.develops_skills if gain["skill_id"] in open_gaps]
        score = 10.0
        closed_critical = [gain for gain in relevant if gain["skill_id"] in critical_ids]
        score += len(closed_critical) * 100
        score += len([gain for gain in relevant if gain["skill_id"] not in critical_ids]) * 30
        if len(relevant) > 1:
            score += 20
        if float(event.duration_hours) <= 8:
            score += 10

        format_history = [item for item in histories if item.event.format == event.format]
        positive = sum(item.status == "completed" for item in format_history)
        negative = sum(item.status in {"no_show", "declined", "dropped"} for item in format_history)
        ratings = [item.feedback_rating for item in format_history if item.feedback_rating]
        score += min(positive * 3, 20)
        score -= min(negative * 10, 40)
        if ratings and sum(ratings) / len(ratings) >= 4:
            score += 8

        unmet = _unmet_prerequisites(event, values)
        if unmet:
            score -= 12
        projected_readiness = readiness_for_values(profile, _projected_values(values, event))
        impact = max(projected_readiness - current_readiness, 0)

        if closed_critical:
            skill_reason = "Closes critical gaps: " + ", ".join(
                open_gaps[item["skill_id"]]["name"] for item in closed_critical
            )
        elif relevant:
            skill_reason = "Develops open gaps: " + ", ".join(
                open_gaps[item["skill_id"]]["name"] for item in relevant[:3]
            )
        else:
            skill_reason = "Supports the target profile without replacing gap-based priorities"

        if negative:
            history_reason = (
                f"Accounts for {negative} declined, dropped or no-show activities in {event.format} format"
            )
        elif positive:
            history_reason = f"Builds on {positive} completed activities in {event.format} format"
        else:
            history_reason = "No repeated negative participation signal for this format"

        payload = serialize_event(event)
        payload.update(
            {
                "score": round(score, 1),
                "locked": bool(unmet),
                "unmet_prerequisites": unmet,
                "quest_chain": _unlock_chain(event, values, goal, events) if unmet else [serialize_event(event)],
                "impact": {
                    "readiness_before": current_readiness,
                    "readiness_after": projected_readiness,
                    "readiness_gain": impact,
                },
                "reasons": [
                    {
                        "group": "goal",
                        "text": f"Matches {goal['target_role']} / {goal['target_grade']}",
                    },
                    {"group": "skills", "text": skill_reason},
                    {"group": "history", "text": history_reason},
                ],
            }
        )
        ranked.append((-score, float(event.duration_hours), event.external_id, payload))

    return [item[-1] for item in sorted(ranked)[:limit]]


def progress(employee: Employee, values: dict[str, int] | None = None) -> dict[str, Any]:
    values = values or effective_skills(employee)
    completed_count = employee.activities.filter(status="completed").count()
    bonus_xp = employee.xp_transactions.aggregate(total=Sum("amount"))["total"] or 0
    xp = completed_count * 200 + int(bonus_xp)
    rank_index = max(index for index, (threshold, _) in enumerate(RANKS) if xp >= threshold)
    threshold, rank = RANKS[rank_index]
    next_threshold = RANKS[rank_index + 1][0] if rank_index + 1 < len(RANKS) else threshold
    next_rank = RANKS[rank_index + 1][1] if rank_index + 1 < len(RANKS) else rank
    improved_count = sum(values.get(skill_id, 0) > int(level) for skill_id, level in employee.skills.items())
    gaps = skill_gap(employee, values)
    score = readiness(employee, values)

    achievements = []
    if completed_count:
        achievements.append({"code": "first_quest", "title": "First Quest"})
    if improved_count >= 5:
        achievements.append({"code": "skill_builder", "title": "Skill Builder"})
    if gaps and not any(item["critical"] and item["gap"] for item in gaps):
        achievements.append({"code": "critical_upgrade", "title": "Critical Upgrade"})
    if score >= 60:
        achievements.append({"code": "career_climber", "title": "Career Climber"})
    if employee.quests.filter(state=EmployeeQuest.State.COMPLETED).exists():
        achievements.append({"code": "quest_master", "title": "Quest Master"})

    return {
        "xp": xp,
        "rank": rank,
        "next_rank": next_rank,
        "rank_floor": threshold,
        "next_rank_xp": next_threshold,
        "achievements": achievements,
        "completed_quests": completed_count,
    }


def career_map(employee: Employee) -> list[dict[str, Any]]:
    goal = employee.career_goal
    nodes = [
        {
            "kind": "current",
            "role": employee.role,
            "grade": employee.grade,
            "label": f"{employee.role} / {employee.grade}",
        }
    ]
    if goal:
        nodes.append(
            {
                "kind": "target",
                "role": goal["target_role"],
                "grade": goal["target_grade"],
                "label": f"{goal['target_role']} / {goal['target_grade']}",
            }
        )
        if goal["target_role"] == employee.role and goal["target_grade"] in GRADE_ORDER:
            index = GRADE_ORDER.index(goal["target_grade"])
            if index + 1 < len(GRADE_ORDER):
                nodes.append(
                    {
                        "kind": "future",
                        "role": goal["target_role"],
                        "grade": GRADE_ORDER[index + 1],
                        "label": f"{goal['target_role']} / {GRADE_ORDER[index + 1]}",
                    }
                )
    return nodes


def quest_groups(employee: Employee) -> dict[str, Any]:
    recommended = recommendations(employee)
    active = []
    seen_active: set[str] = set()
    for quest in employee.quests.filter(state=EmployeeQuest.State.ACTIVE).select_related("event"):
        active.append({**serialize_event(quest.event), "state": "active", "started_at": quest.started_at.isoformat()})
        seen_active.add(quest.event_id)
    for item in employee.activities.filter(status="in_progress").select_related("event"):
        if item.event_id not in seen_active:
            active.append(
                {
                    **serialize_event(item.event),
                    "state": "active",
                    "progress": item.completion_pct,
                    "started_at": item.date.isoformat(),
                }
            )
            seen_active.add(item.event_id)

    completed = []
    seen_completed: set[str] = set()
    for item in (
        employee.activities.filter(status="completed").select_related("event").order_by("-date")[:30]
    ):
        if item.event_id in seen_completed:
            continue
        completed.append(
            {
                **serialize_event(item.event),
                "state": "completed",
                "completed_at": item.date.isoformat(),
            }
        )
        seen_completed.add(item.event_id)
        if len(completed) >= 10:
            break
    return {"recommended": recommended, "active": active, "completed": completed}


def dashboard(employee: Employee) -> dict[str, Any]:
    values = effective_skills(employee)
    gaps = skill_gap(employee, values)
    recs = recommendations(employee)
    active_quest = employee.quests.filter(state=EmployeeQuest.State.ACTIVE).select_related("event").first()
    return {
        "employee": serialize_employee(employee),
        "career_goal": employee.career_goal,
        "readiness": readiness(employee, values),
        "top_gaps": [item for item in gaps if item["gap"] > 0][:5],
        "active_quest": serialize_event(active_quest.event) if active_quest else None,
        "next_quest": recs[0] if recs else None,
        "progress": progress(employee, values),
        "career_map": career_map(employee),
    }


def skills_payload(employee: Employee) -> dict[str, Any]:
    values = effective_skills(employee)
    baseline = {key: int(value) for key, value in employee.skills.items()}
    gaps = skill_gap(employee, values)
    return {
        "employee_id": employee.external_id,
        "career_goal": employee.career_goal,
        "readiness": readiness(employee, values),
        "skills": [
            {
                **item,
                "baseline": baseline.get(item["skill_id"], 0),
                "improved_after_review": values.get(item["skill_id"], 0) > baseline.get(item["skill_id"], 0),
            }
            for item in gaps
        ],
    }


def career_payload(employee: Employee) -> dict[str, Any]:
    values = effective_skills(employee)
    return {
        "employee_id": employee.external_id,
        "current": {"role": employee.role, "grade": employee.grade},
        "goal": employee.career_goal,
        "readiness": readiness(employee, values),
        "gaps": [item for item in skill_gap(employee, values) if item["gap"] > 0],
        "career_map": career_map(employee),
    }


def hr_overview() -> dict[str, Any]:
    gap_counts: Counter[tuple[str, str, bool]] = Counter()
    no_goal = []
    without_next_step = []
    events = list(LearningEvent.objects.all())
    for employee in Employee.objects.all():
        if not employee.career_goal:
            no_goal.append(serialize_employee(employee))
            continue
        for gap in skill_gap(employee):
            if gap["gap"] > 0:
                gap_counts[(gap["skill_id"], gap["name"], gap["critical"])] += 1
        if not recommendations(employee, limit=1, event_pool=events):
            without_next_step.append(serialize_employee(employee))

    participation = Counter(ActivityHistory.objects.values_list("status", flat=True))
    top_gaps = [
        {"skill_id": skill_id, "name": name, "critical": critical, "employees": count}
        for (skill_id, name, critical), count in gap_counts.most_common(12)
    ]
    return {
        "top_gaps": top_gaps,
        "employees_without_goal": no_goal,
        "employees_without_next_step": without_next_step,
        "participation": dict(sorted(participation.items())),
        "totals": {
            "employees": Employee.objects.count(),
            "events": LearningEvent.objects.count(),
            "activity_records": ActivityHistory.objects.count(),
        },
    }
