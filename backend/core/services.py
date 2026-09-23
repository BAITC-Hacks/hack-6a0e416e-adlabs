from collections import defaultdict
from django.conf import settings

from .models import ActivityHistory, LearningEvent, RoleProfile, Skill


def effective_skills(baseline, last_review_date, activities):
    """Apply only completed activity gains after the last assessment."""
    levels = dict(baseline)
    for activity in sorted(activities, key=lambda a: (a["date"], a["id"])):
        if activity["status"] != "completed" or activity["date"] <= last_review_date:
            continue
        for gain in activity["develops_skills"]:
            skill = gain["skill_id"]
            levels[skill] = min(levels.get(skill, 0) + gain["gain"], gain.get("max_level", 5), 5)
    return levels


def gap_and_readiness(levels, required, critical, critical_weight=2):
    gaps = []
    earned = total = 0.0
    for skill_id, target in required.items():
        if not target or target < 0:
            continue
        current = levels.get(skill_id, 0)
        is_critical = skill_id in critical
        weight = critical_weight if is_critical else 1
        earned += min(current / target, 1) * weight
        total += weight
        gaps.append({"skill_id": skill_id, "current": current, "required": target,
                     "gap": max(target - current, 0), "critical": is_critical})
    return gaps, round(100 * earned / total) if total else 0


def event_applicable(event, role, grade):
    return (not event["target_roles"] or role in event["target_roles"]) and (
        not event["target_grades"] or grade in event["target_grades"])


def rank_events(events, levels, gaps, role, grade, completed_ids, active_ids):
    """Return stable ranked recommendations, including explainable locked entries."""
    needed = {item["skill_id"]: item for item in gaps if item["gap"] > 0}
    result = []
    for event in events:
        if event["mandatory"] or not event_applicable(event, role, grade):
            continue
        if event["event_id"] in active_ids or (event["event_id"] in completed_ids and not event["repeatable"]):
            continue
        covered = [gain["skill_id"] for gain in event["develops_skills"]
                   if gain["skill_id"] in needed and min(
                       levels.get(gain["skill_id"], 0) + gain["gain"], gain.get("max_level", 5)
                   ) > levels.get(gain["skill_id"], 0)]
        if not covered:
            continue
        unmet = [{"skill_id": skill, "current": levels.get(skill, 0), "required": value}
                 for skill, value in event["prerequisites"].items() if levels.get(skill, 0) < value]
        score = sum(100 if needed[s]["critical"] else 30 for s in covered)
        if len(covered) > 1:
            score += 20
        score += max(0, 10 - int(event["duration_hours"] // 4))
        reasons = [{"code": "CRITICAL_GAP" if needed[s]["critical"] else "SKILL_GAP",
                    "skill_id": s, "gap": needed[s]["gap"]} for s in covered]
        result.append({**event, "score": score, "reasons": reasons, "locked": bool(unmet),
                       "unmet_prerequisites": unmet, "covered_skills": covered})
    return sorted(result, key=lambda x: (-x["score"], x["event_id"]))


def prerequisite_chain(target, events, levels, max_depth=3):
    """Find a bounded, cycle-safe learning path ending at the target event."""
    by_id = {e["event_id"]: e for e in events}

    def visit(event_id, current, seen, depth):
        if event_id in seen or depth > max_depth:
            return None
        event = by_id[event_id]
        missing = [(s, n) for s, n in event["prerequisites"].items() if current.get(s, 0) < n]
        if not missing:
            return [event_id], current
        chain = []
        seen = seen | {event_id}
        for skill, required in missing:
            candidates = [e for e in events if not e["mandatory"] and e["event_id"] not in seen
                          and any(g["skill_id"] == skill and min(current.get(skill, 0) + g["gain"],
                          g.get("max_level", 5)) >= required for g in e["develops_skills"])]
            candidates.sort(key=lambda e: (e["duration_hours"], e["event_id"]))
            found = None
            for candidate in candidates:
                found = visit(candidate["event_id"], current, seen, depth + 1)
                if found:
                    break
            if not found:
                return None
            prior, current = found
            chain.extend(prior)
            for gain in candidate["develops_skills"]:
                sid = gain["skill_id"]
                current[sid] = min(current.get(sid, 0) + gain["gain"], gain.get("max_level", 5))
        return list(dict.fromkeys(chain + [event_id])), current

    found = visit(target["event_id"], dict(levels), set(), 1)
    return found[0] if found else []


def serialize_event(event):
    return {"event_id": event.external_id, "title": event.title,
            "description": event.description, "duration_hours": event.duration_hours,
            "format": event.format, "mandatory": event.mandatory, "repeatable": event.repeatable,
            "target_roles": event.target_roles, "target_grades": event.target_grades,
            "develops_skills": event.develops_skills, "prerequisites": event.prerequisites}


def career_snapshot(employee):
    events = [serialize_event(e) for e in LearningEvent.objects.all().order_by("external_id")]
    activities = [
        {"id": a.external_id, "date": a.date, "status": a.status,
         "develops_skills": a.event.develops_skills, "event_id": a.event.external_id}
        for a in ActivityHistory.objects.filter(employee=employee).select_related("event")]
    levels = effective_skills(employee.baseline_skills, employee.last_review_date, activities)
    completed = {a["event_id"] for a in activities if a["status"] == "completed"}
    active = {a["event_id"] for a in activities if a["status"] == "in_progress"}
    active |= set(employee.quests.filter(state="active").values_list("event__external_id", flat=True))
    goal = employee.career_goal
    profile = RoleProfile.objects.filter(role=goal["target_role"], grade=goal["target_grade"]).first() if goal else None
    gaps, readiness = gap_and_readiness(levels, profile.required_skills, profile.critical_skills,
                                        settings.CRITICAL_SKILL_WEIGHT) if profile else ([], None)
    recommendations = rank_events(events, levels, gaps, goal["target_role"], goal["target_grade"],
                                  completed, active) if goal and profile else []
    for item in recommendations:
        item["chain"] = prerequisite_chain(item, events, levels) if item["locked"] else [item["event_id"]]
        projected = dict(levels)
        for gain in item["develops_skills"]:
            sid = gain["skill_id"]
            projected[sid] = min(projected.get(sid, 0) + gain["gain"], gain.get("max_level", 5))
        item["readiness_after"] = gap_and_readiness(
            projected, profile.required_skills, profile.critical_skills,
            settings.CRITICAL_SKILL_WEIGHT)[1]
    names = dict(Skill.objects.values_list("external_id", "name"))
    for gap in gaps:
        gap["name"] = names.get(gap["skill_id"], gap["skill_id"])
    for item in recommendations:
        item["skills"] = [names.get(s, s) for s in item["covered_skills"]]
    xp = sum(employee.xp_transactions.values_list("amount", flat=True))
    ranks = ["Explorer", "Practitioner", "Specialist", "Expert", "Master"]
    rank = ranks[min(xp // 600, len(ranks) - 1)]
    quests = list(employee.quests.select_related("event").order_by("-started_at"))
    completed_quests = [q for q in quests if q.state == "completed"]
    improved = sum(1 for sid, level in levels.items() if level > employee.baseline_skills.get(sid, 0))
    baseline_readiness = gap_and_readiness(
        employee.baseline_skills, profile.required_skills, profile.critical_skills,
        settings.CRITICAL_SKILL_WEIGHT)[1] if profile else 0
    achievements = []
    if completed_quests:
        achievements.append("FIRST_QUEST")
    if improved >= 5:
        achievements.append("SKILL_BUILDER")
    if any(g["critical"] and employee.baseline_skills.get(g["skill_id"], 0) < g["required"]
           and levels.get(g["skill_id"], 0) >= g["required"] for g in gaps):
        achievements.append("CRITICAL_UPGRADE")
    if readiness is not None and readiness - baseline_readiness >= 20:
        achievements.append("CAREER_CLIMBER")
    if any(q.event.prerequisites for q in completed_quests):
        achievements.append("QUEST_MASTER")
    if goal and goal["target_role"] != employee.role:
        achievements.append("CROSS_PATH_EXPLORER")
    active_quests = {a["event_id"]: {"event_id": a["event_id"],
                    "title": next((e["title"] for e in events if e["event_id"] == a["event_id"]), a["event_id"]),
                    "state": "active"} for a in activities if a["status"] == "in_progress"}
    completed_quest_items = {a["event_id"]: {"event_id": a["event_id"],
                    "title": next((e["title"] for e in events if e["event_id"] == a["event_id"]), a["event_id"]),
                    "state": "completed", "xp": 0} for a in activities if a["status"] == "completed"}
    for q in quests:
        item = {"event_id": q.event.external_id, "title": q.event.title, "state": q.state}
        if q.state == "active":
            active_quests[q.event.external_id] = item
        else:
            active_quests.pop(q.event.external_id, None)
            completed_quest_items[q.event.external_id] = {**item, "xp": q.xp_awarded}
    return {"employee": {"id": employee.external_id, "name": employee.full_name,
                         "role": employee.role, "grade": employee.grade,
                         "department": employee.department},
            "goal": goal, "effective_skills": levels, "gaps": gaps, "readiness": readiness,
            "recommendations": recommendations, "active_quests": list(active_quests.values()),
            "completed_quests": list(completed_quest_items.values()),
            "xp": xp, "rank": rank, "achievements": achievements, "skill_names": names}
