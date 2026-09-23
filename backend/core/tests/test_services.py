from datetime import date
from core.services import effective_skills, gap_and_readiness, rank_events, prerequisite_chain


def test_effective_skills_only_new_completed_and_cap():
    activities = [
        {"id": "1", "date": date(2026, 1, 1), "status": "completed",
         "develops_skills": [{"skill_id": "A", "gain": 2, "max_level": 5}]},
        {"id": "2", "date": date(2026, 2, 2), "status": "in_progress",
         "develops_skills": [{"skill_id": "A", "gain": 2, "max_level": 5}]},
        {"id": "3", "date": date(2026, 2, 3), "status": "completed",
         "develops_skills": [{"skill_id": "A", "gain": 4, "max_level": 4}]},
    ]
    assert effective_skills({"A": 2}, date(2026, 2, 1), activities) == {"A": 4}


def test_gap_readiness_critical_weight_and_bounds():
    gaps, readiness = gap_and_readiness({"A": 1, "B": 9}, {"A": 2, "B": 3, "C": 0}, {"A"})
    assert readiness == 67
    assert [g["gap"] for g in gaps] == [1, 0]
    assert 0 <= readiness <= 100


def test_recommendations_filter_and_stable_order():
    base = {"description": "", "duration_hours": 2, "format": "online", "repeatable": False,
            "target_roles": [], "target_grades": [], "develops_skills": [
                {"skill_id": "A", "gain": 1, "max_level": 5}], "prerequisites": {}}
    events = [
        {**base, "event_id": "C", "title": "C", "mandatory": True},
        {**base, "event_id": "B", "title": "B", "mandatory": False},
        {**base, "event_id": "A", "title": "A", "mandatory": False},
    ]
    gaps = [{"skill_id": "A", "gap": 2, "critical": True}]
    first = rank_events(events, {}, gaps, "Engineer", "Middle", set(), set())
    assert [x["event_id"] for x in first] == ["A", "B"]
    assert rank_events(events, {}, gaps, "Engineer", "Middle", set(), set()) == first
    assert [x["event_id"] for x in rank_events(events, {}, gaps, "Engineer", "Middle", {"A"}, set())] == ["B"]


def test_locked_event_has_chain_and_cycle_protection():
    base = {"mandatory": False, "duration_hours": 2, "prerequisites": {}}
    events = [
        {**base, "event_id": "foundation", "develops_skills": [{"skill_id": "A", "gain": 1, "max_level": 5}]},
        {**base, "event_id": "target", "prerequisites": {"A": 1},
         "develops_skills": [{"skill_id": "B", "gain": 1, "max_level": 5}]},
    ]
    assert prerequisite_chain(events[1], events, {}) == ["foundation", "target"]
    events[0]["prerequisites"] = {"B": 1}
    assert prerequisite_chain(events[1], events, {}) == []
