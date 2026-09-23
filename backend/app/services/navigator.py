"""Thin stateful navigator around the pure recommendation engine."""

import math
import re

from ml import engine

from ..data import Dataset
from .ai_provider import BaseAIProvider


def get_employee_profile(data: Dataset, employee_id: str) -> dict:
    employee = dict(data.employees[employee_id])
    employee["skills"] = dict(data.effective_skills[employee_id])
    return {"employee": employee, "target": engine.resolve_target(employee, data.role_profiles)}


def calculate_skill_gap(data: Dataset, employee_id: str) -> dict:
    employee = data.employees[employee_id]
    return engine.calculate_skill_gap(
        employee, data.effective_skills[employee_id], data.catalog, data.role_profiles
    )


def _explain(recommendations: list[dict], target: dict | None, provider: BaseAIProvider) -> list[dict]:
    # Copy engine output, preserving its ranking and scores.
    return [{**item, "explanation": provider.explain(item, target)} for item in recommendations]


def recommend_activities(data: Dataset, employee_id: str, provider: BaseAIProvider) -> dict:
    employee = data.employees[employee_id]
    target = engine.resolve_target(employee, data.role_profiles)
    items = engine.recommend_activities(
        employee, data.effective_skills[employee_id], data.catalog, data.role_profiles,
        list(data.events.values()), data.history, data.as_of_date,
        completed_event_ids=data.session_completions[employee_id], limit=3,
    )
    return {"employee_id": employee_id, "target": target, "recommendations": _explain(items, target, provider)}


def build_roadmap(data: Dataset, employee_id: str, provider: BaseAIProvider) -> dict:
    employee = data.employees[employee_id]
    roadmap = engine.build_roadmap(
        employee, data.effective_skills[employee_id], data.catalog, data.role_profiles,
        list(data.events.values()), data.history, data.as_of_date,
        completed_event_ids=data.session_completions[employee_id], limit=3,
    )
    target = roadmap["target"]
    return {
        **roadmap,
        "steps": [
            {**step, "recommendation": _explain([step["recommendation"]], target, provider)[0]}
            for step in roadmap["steps"]
        ],
    }


def simulate_activity_completion(data: Dataset, employee_id: str, event_id: str, provider: BaseAIProvider) -> dict:
    employee = data.employees[employee_id]
    event = data.events[event_id]
    target = engine.resolve_target(employee, data.role_profiles)
    skills = data.effective_skills[employee_id]
    updated, applied = engine.apply_event_gains(event, skills)
    data.effective_skills[employee_id] = updated
    data.session_completions[employee_id].add(event_id)
    data.activity_statuses[employee_id][event_id] = "completed"
    return {
        "employee_id": employee_id,
        "event_id": event_id,
        "applied_skill_gains": applied,
        "skill_gap": calculate_skill_gap(data, employee_id),
        "recommendations": recommend_activities(data, employee_id, provider)["recommendations"],
        "roadmap": build_roadmap(data, employee_id, provider),
    }


def activity_details(data: Dataset, employee_id: str, event_id: str, provider: BaseAIProvider) -> dict:
    employee = data.employees[employee_id]
    event = data.events[event_id]
    skills = data.effective_skills[employee_id]
    names = {skill["skill_id"]: skill["name"] for skill in data.catalog}
    target = engine.resolve_target(employee, data.role_profiles)
    eligible = engine.event_is_eligible(
        event, employee, skills, target, data.history_for(employee_id), data.as_of_date,
        completed_event_ids=data.session_completions[employee_id],
    )
    recommendations = engine.recommend_activities(
        employee, skills, data.catalog, data.role_profiles, list(data.events.values()),
        data.history, data.as_of_date, completed_event_ids=data.session_completions[employee_id],
        limit=len(data.events),
    )
    recommendation = next((item for item in recommendations if item["event_id"] == event_id), None)
    if recommendation:
        recommendation = _explain([recommendation], target, provider)[0]
    future = sorted(day for day in event["upcoming_sessions"] if day >= data.as_of_date)
    return {
        "employee_id": employee_id, "event_id": event_id,
        "title": event["title"], "description": event["description"],
        "type": event["type"], "format": event["format"],
        "duration_hours": event["duration_hours"], "upcoming_sessions": future,
        "next_session_date": future[0] if future and event["format"] != "self_paced" else None,
        "prerequisites": [
            {"skill_id": skill_id, "name": names[skill_id], "current_level": skills.get(skill_id, 0),
             "required_level": level, "met": skills.get(skill_id, 0) >= level}
            for skill_id, level in event["prerequisites"].items()
        ],
        "develops_skills": [
            {"skill_id": gain["skill_id"], "name": names[gain["skill_id"]],
             "current_level": skills.get(gain["skill_id"], 0), "gain": gain["gain"],
             "max_level": gain["max_level"]}
            for gain in event["develops_skills"]
        ],
        "external_url": event.get("external_url"), "provider_url": event.get("provider_url"),
        "status": data.activity_status(employee_id, event_id), "eligible": eligible,
        "recommendation": recommendation,
    }


def ask_navigator(data: Dataset, employee_id: str, question: str, intent: str | None,
                  event_id: str | None, weekly_hours: float | None, provider: BaseAIProvider) -> dict:
    employee = data.employees[employee_id]
    gap = calculate_skill_gap(data, employee_id)
    recommendations = recommend_activities(data, employee_id, provider)["recommendations"]
    roadmap = build_roadmap(data, employee_id, provider)
    lower = question.lower()
    hours_match = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:час|hour)", lower)
    if intent is None:
        intent = ("after_activity" if any(word in lower for word in ("после", "изменится", "заверш")) else
                  "blockers" if any(word in lower for word in ("мешает", "барьер", "разрыв")) else
                  "four_hours" if hours_match else
                  "faster_route" if any(word in lower for word in ("быстр", "маршрут")) else
                  "why_course" if any(word in lower for word in ("почему", "курс", "активност")) else
                  "first_skill" if any(word in lower for word in ("перв", "навык")) else "general")
    top = recommendations[0] if recommendations else None
    if event_id:
        all_recommendations = engine.recommend_activities(
            employee, data.effective_skills[employee_id], data.catalog, data.role_profiles,
            list(data.events.values()), data.history, data.as_of_date,
            completed_event_ids=data.session_completions[employee_id], limit=len(data.events),
        )
        selected = next((item for item in all_recommendations if item["event_id"] == event_id), None)
    else:
        selected = top
    open_skills = [skill for skill in gap["skills"] if skill["gap"] > 0]
    first = open_skills[0] if open_skills else None
    target = gap["target"]
    facts = [f"{employee['full_name']}: {employee['role']} {employee['grade']}."]
    if target:
        facts.append(f"Цель: {target['role']} {target['grade']}; готовность {gap['progress_pct']}%.")
    evidence = [employee_id] + ([first["skill_id"]] if first else []) + ([selected["event_id"]] if selected else [])
    if not target:
        summary = "Для этого профиля карьерная цель пока не задана."
        reason = "Автоматический переход после Lead не определён."
        effect = "Без цели нельзя посчитать целевой разрыв и прогноз."
        next_step = "Задайте карьерную цель в исходных данных профиля."
    elif gap["status"] == "ready":
        summary = "Все требования выбранной цели уже выполнены."
        reason = "Разрыв по целевым навыкам равен нулю."
        effect = "Дополнительная активность не увеличит готовность к этой цели."
        next_step = "Обсудите следующий карьерный шаг с руководителем."
    elif not selected:
        summary = "Есть разрыв навыков, но сейчас нет подходящей активности."
        reason = f"Осталось {gap['total_gap_points']} баллов разрыва."
        effect = "Прогноз по активности недоступен."
        next_step = f"Начните с навыка {first['name']} ({first['current_level']} из {first['required_level']})." if first else "Проверьте целевой профиль."
    else:
        matched = selected["matched_skill_gains"]
        names = ", ".join(f"{skill['name']} (+{skill['gap_closed']})" for skill in matched[:3])
        reason = f"{selected['title']} сокращает разрыв по навыкам: {names}."
        effect = f"После выполнения прогноз готовности: {selected['projected_impact']['progress_after_pct']}% (+{selected['projected_impact']['progress_delta_pct']} п.п.)."
        next_step = f"Откройте детали {selected['title']} и проверьте условия участия."
        if intent == "blockers":
            summary = f"Главный барьер: {first['name']} — разрыв {first['gap']} по шкале навыка." if first else "Разрыв невелик."
            reason = f"Всего открыто {len(open_skills)} навыков; критичный разрыв — {gap['critical_gap_points']} балл."
        elif intent == "first_skill":
            summary = f"Начните с {first['name']}: сейчас {first['current_level']}, требуется {first['required_level']}." if first else "Нет открытых навыков."
        elif intent == "after_activity":
            summary = f"После {selected['title']} готовность может вырасти до {selected['projected_impact']['progress_after_pct']}%."
        elif intent == "faster_route":
            summary = f"Первый шаг маршрута — {roadmap['steps'][0]['recommendation']['title']}." if roadmap["steps"] else "Маршрут пока пуст."
            reason = f"Маршрут последовательно пересчитывает до {len(roadmap['steps'])} шагов."
        elif intent == "four_hours":
            parsed_hours = float(hours_match.group(1).replace(",", ".")) if hours_match else None
            hours = weekly_hours or (parsed_hours if parsed_hours and 0 < parsed_hours <= 80 else 4)
            weeks = math.ceil(selected["duration_hours"] / hours)
            summary = f"При {hours:g} ч в неделю на {selected['title']} потребуется минимум {weeks} нед."
            effect += " Это оценка только по длительности активности."
        else:
            summary = f"Рекомендую начать с {selected['title']}."
    limitation = "Прогноз основан на данных датасета и не гарантирует повышение; действия в демо хранятся до перезапуска API."
    result = {"employee_id": employee_id, "provider": "template", "intent": intent,
              "summary": summary, "profile_facts": facts, "reason": reason,
              "expected_effect": effect, "limitation": limitation, "next_step": next_step,
              "evidence_ids": list(dict.fromkeys(evidence))}
    return result
