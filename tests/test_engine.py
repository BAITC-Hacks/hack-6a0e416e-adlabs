"""Behavioral checks for the deterministic recommendation rules."""

import csv
import json
from pathlib import Path

import pytest

from ml.engine import (
    apply_event_gains,
    build_roadmap,
    calculate_skill_gap,
    event_is_eligible,
    recommend_activities,
    resolve_target,
)


def sample_data():
    root = Path(__file__).resolve().parents[1] / "datasets" / "career_quest"
    skills = json.loads((root / "skills.json").read_text(encoding="utf-8"))
    events = json.loads((root / "events.json").read_text(encoding="utf-8"))
    employees = json.loads((root / "employees.json").read_text(encoding="utf-8"))
    with (root / "activity_history.csv").open(newline="", encoding="utf-8") as source:
        history = list(csv.DictReader(source))
    assert skills["meta"]["as_of_date"] == events["meta"]["as_of_date"]
    return skills, events, employees, history


def tiny_data():
    employee = {"employee_id": "E1", "role": "Engineer", "grade": "Junior", "career_goal": None}
    catalog = [
        {"skill_id": "A", "name": "Architecture", "type": "hard", "category": "engineering"},
        {"skill_id": "B", "name": "Writing", "type": "soft", "category": "communication"},
    ]
    profiles = [
        {"role": "Engineer", "grade": "Middle", "required_skills": {"A": 3, "B": 2}, "critical_skills": ["A"]},
        {"role": "Designer", "grade": "Senior", "required_skills": {"B": 3}, "critical_skills": ["B"]},
    ]
    base = {
        "description": "Practice", "type": "course", "format": "self_paced",
        "duration_hours": 2, "mandatory": False, "target_roles": ["Engineer"],
        "target_grades": ["Middle"], "prerequisites": {}, "upcoming_sessions": [],
    }
    first = dict(base, event_id="EV_001", title="Architecture", develops_skills=[{"skill_id": "A", "gain": 2, "max_level": 3}])
    second = dict(base, event_id="EV_002", title="Writing", develops_skills=[{"skill_id": "B", "gain": 2, "max_level": 2}])
    return employee, catalog, profiles, [first, second]


def test_target_and_gap_rules():
    employee, catalog, profiles, _ = tiny_data()
    assert resolve_target(employee, profiles) == {"role": "Engineer", "grade": "Middle", "source": "next_grade"}
    gap = calculate_skill_gap(employee, {"A": 5}, catalog, profiles)
    assert (gap["progress_pct"], gap["total_met_points"], gap["total_gap_points"]) == (60.0, 3, 2)
    assert gap["skills"][0]["skill_id"] == "A"  # critical-first even when met
    assert gap["critical_gap_points"] == 0
    employee["career_goal"] = {"target_role": "Designer", "target_grade": "Senior"}
    assert calculate_skill_gap(employee, {}, catalog, profiles)["target"]["source"] == "career_goal"
    employee["career_goal"] = None
    employee["grade"] = "Lead"
    assert calculate_skill_gap(employee, {}, catalog, profiles)["progress_pct"] is None


def test_eligibility_and_score_use_actual_history_and_caps():
    employee, catalog, profiles, events = tiny_data()
    target = resolve_target(employee, profiles)
    history = [
        {"employee_id": "X", "event_id": "EV_001", "status": "completed"},
        {"employee_id": "X", "event_id": "EV_001", "status": "dropped"},
        {"employee_id": "E1", "event_id": "EV_002", "status": "dropped"},
    ]
    assert event_is_eligible(events[0], employee, {}, target, history, "2026-10-01")
    recommended = recommend_activities(employee, {}, catalog, profiles, events, history, "2026-10-01")
    assert [item["event_id"] for item in recommended] == ["EV_001", "EV_002"]
    top = recommended[0]
    assert top["score_breakdown"] == {
        "critical_skill_coverage": 30.0, "total_gap_coverage": 10.0,
        "career_goal_alignment": 15.0, "completion_likelihood": 5.0,
        "time_efficiency": 5.0,
    }
    assert top["score"] == 65.0
    assert top["projected_impact"]["progress_delta_pct"] == 40.0
    assert "Engineer Middle" in top["explanation"]
    capped, gains = apply_event_gains(events[0], {"A": 5})
    assert capped["A"] == 5 and gains[0]["gain"] == 0
    assert recommend_activities(employee, {"A": 5, "B": 2}, catalog, profiles, events, history, "2026-10-01") == []


def test_roadmap_is_sequential_distinct_and_pure():
    employee, catalog, profiles, events = tiny_data()
    original = {}
    roadmap = build_roadmap(employee, original, catalog, profiles, events, [], "2026-10-01")
    assert [step["recommendation"]["event_id"] for step in roadmap["steps"]] == ["EV_001", "EV_002"]
    assert roadmap["status"] == "no_activities"  # one architecture point remains
    assert roadmap["ending_progress_pct"] == 80.0
    assert original == {}
    assert roadmap["steps"][1]["progress_before_pct"] == 40.0


def test_session_completed_repeatable_and_cross_role():
    employee, catalog, profiles, events = tiny_data()
    event = dict(events[0], format="online", upcoming_sessions=["2026-09-30", "2026-10-05"])
    assert event_is_eligible(event, employee, {}, resolve_target(employee, profiles), [], "2026-10-01")
    assert not event_is_eligible(event, employee, {}, resolve_target(employee, profiles), [], "2026-10-06")
    assert not event_is_eligible(event, employee, {}, resolve_target(employee, profiles), [], "2026-10-01", {"EV_001"})
    event["event_id"] = "EV_036"
    assert event_is_eligible(event, employee, {}, resolve_target(employee, profiles), [{"employee_id": "E1", "event_id": "EV_036", "status": "completed"}], "2026-10-01", {"EV_036"})
    employee["career_goal"] = {"target_role": "Designer", "target_grade": "Senior"}
    event["target_roles"] = ["Designer"]
    event["target_grades"] = ["Senior"]
    assert event_is_eligible(event, employee, {}, resolve_target(employee, profiles), [], "2026-10-01")


def test_real_dataset_smoke():
    skills_data, events_data, employees_data, history = sample_data()
    catalog = skills_data["skills"]
    profiles = skills_data["role_profiles"]
    events = events_data["events"]
    as_of_date = skills_data["meta"]["as_of_date"]
    for employee in employees_data["employees"][:10]:
        recommendations = recommend_activities(employee, employee["skills"], catalog, profiles, events, history, as_of_date)
        roadmap = build_roadmap(employee, employee["skills"], catalog, profiles, events, history, as_of_date)
        assert len(recommendations) <= 3
        assert len(roadmap["steps"]) <= 3
        assert len({step["recommendation"]["event_id"] for step in roadmap["steps"]}) == len(roadmap["steps"])
        assert all(recommendations[index]["score"] >= recommendations[index + 1]["score"] for index in range(len(recommendations) - 1))


def test_duplicate_developed_skill_cannot_inflate_score():
    employee, catalog, profiles, events = tiny_data()
    events[0]["develops_skills"].append({"skill_id": "A", "gain": 1, "max_level": 3})
    with pytest.raises(ValueError, match="Duplicate developed skill"):
        recommend_activities(employee, {}, catalog, profiles, events, [], "2026-10-01")
