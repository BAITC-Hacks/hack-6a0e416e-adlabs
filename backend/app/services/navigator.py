"""Thin stateful navigator around the pure recommendation engine."""

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
    return {
        "employee_id": employee_id,
        "event_id": event_id,
        "applied_skill_gains": applied,
        "skill_gap": calculate_skill_gap(data, employee_id),
        "recommendations": recommend_activities(data, employee_id, provider)["recommendations"],
        "roadmap": build_roadmap(data, employee_id, provider),
    }
