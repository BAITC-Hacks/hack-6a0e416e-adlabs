"""API contract smoke tests against the supplied synthetic dataset."""

import json
import shutil

from fastapi.testclient import TestClient

from backend.app.data import DEFAULT_DATA_DIR, DatasetError, load_dataset
from backend.app.main import app
from backend.app.services.ai_provider import OpenAIProvider, TemplateAIProvider


def test_dataset_loads_from_any_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    data = load_dataset()
    assert data.as_of_date == "2026-10-01"
    assert len(data.employees) == 200


def test_invalid_source_fails_validation(tmp_path):
    for source in DEFAULT_DATA_DIR.iterdir():
        if source.is_file() and source.suffix in {".json", ".csv"}:
            shutil.copy2(source, tmp_path / source.name)
    path = tmp_path / "events.json"
    events = json.loads(path.read_text(encoding="utf-8"))
    events["events"][0]["duration_hours"] = 0
    path.write_text(json.dumps(events), encoding="utf-8")
    try:
        load_dataset(tmp_path)
    except DatasetError as exc:
        assert "duration" in str(exc)
    else:
        raise AssertionError("Invalid event duration was accepted")


def test_template_explanation_does_not_invent_critical_gap():
    recommendation = {
        "matched_skill_gains": [{"name": "Writing", "current_level": 1, "projected_level": 2,
                                 "gap_closed": 1, "critical": False}],
        "score_breakdown": {"critical_skill_coverage": 45.0},
        "projected_impact": {"progress_delta_pct": 5.0},
    }
    explanation = TemplateAIProvider().explain(recommendation, {"role": "Engineer", "grade": "Middle"})
    assert "target gap coverage" in explanation
    assert "critical skill coverage" not in explanation


def test_endpoints_and_simulated_completion():
    app.state.dataset = load_dataset()
    app.state.data_error = None
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["dataset"] == {"employees": 200, "events": 40, "skills": 60, "role_profiles": 32}
    employees = client.get("/api/employees")
    assert employees.status_code == 200
    assert len(employees.json()["employees"]) == 200
    employee_id = "E0001"
    profile = client.get(f"/api/employees/{employee_id}")
    assert profile.status_code == 200
    assert profile.json()["target"]["grade"] == "Middle"
    gap = client.get(f"/api/employees/{employee_id}/skill-gap")
    assert gap.status_code == 200
    assert gap.json()["employee_id"] == employee_id
    recommendations = client.get(f"/api/employees/{employee_id}/recommendations")
    assert recommendations.status_code == 200
    assert len(recommendations.json()["recommendations"]) <= 3
    roadmap = client.get(f"/api/employees/{employee_id}/roadmap")
    assert roadmap.status_code == 200
    assert len(roadmap.json()["steps"]) <= 3
    assert client.get("/api/hr/overview").json()["employee_count"] == 200
    assert client.get("/api/employees/E9999").json()["error"]["code"] == "not_found"
    assert client.post("/api/employees/E0016/activities/EV_001/complete").status_code == 422
    if recommendations.json()["recommendations"]:
        event_id = recommendations.json()["recommendations"][0]["event_id"]
        completed = client.post(f"/api/employees/{employee_id}/activities/{event_id}/complete")
        assert completed.status_code == 200, completed.text
        assert completed.json()["skill_gap"]["total_gap_points"] <= gap.json()["total_gap_points"]
        if event_id != "EV_036":
            again = client.post(f"/api/employees/{employee_id}/activities/{event_id}/complete")
            assert again.status_code == 409


def test_activity_lifecycle_and_navigator_are_grounded(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    data = load_dataset()
    app.state.dataset = data
    app.state.data_error = None
    client = TestClient(app)
    employee_id = "E0001"
    before = client.get(f"/api/employees/{employee_id}/skill-gap").json()
    rec = client.get(f"/api/employees/{employee_id}/recommendations").json()["recommendations"][0]
    event_id = rec["event_id"]
    path = f"/api/employees/{employee_id}/activities/{event_id}"
    details = client.get(path)
    assert details.status_code == 200
    assert details.json()["eligible"] is True
    assert details.json()["external_url"] is None
    assert details.json()["recommendation"]["projected_impact"] == rec["projected_impact"]
    answer = client.post(f"/api/employees/{employee_id}/navigator/ask", json={
        "question": "Что изменится после активности?", "intent": "after_activity", "event_id": event_id,
    })
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["provider"] == "template"
    assert body["evidence_ids"][0] == employee_id and event_id in body["evidence_ids"]
    assert all(identifier == employee_id or identifier in data.events or
               any(skill["skill_id"] == identifier for skill in data.catalog) for identifier in body["evidence_ids"])
    assert client.get(f"/api/employees/{employee_id}/skill-gap").json() == before
    assert client.post(f"{path}/actions/start").status_code == 409
    assert client.post(f"{path}/actions/enroll").json()["status"] == "enrolled"
    assert client.post(f"{path}/actions/start").json()["status"] == "in_progress"
    assert client.get(path).json()["status"] == "in_progress"
    completed = client.post(f"{path}/complete")
    assert completed.status_code == 200
    assert completed.json()["activity_status"] == "completed"
    assert completed.json()["skill_gap"]["total_gap_points"] <= before["total_gap_points"]
    assert client.get(path).json()["status"] == "completed"
    history = client.get(f"/api/employees/{employee_id}/activity-history").json()["activities"]
    assert history[0]["source"] == "demo" and history[0]["status"] == "completed"
    assert all(item["event_id"] in data.events for item in history)
    assert client.post(f"{path}/actions/enroll").status_code == 409


def test_no_target_ready_blocked_and_empty_recommendations():
    data = load_dataset()
    app.state.dataset = data
    app.state.data_error = None
    client = TestClient(app)
    no_goal = next(employee_id for employee_id, employee in data.employees.items()
                   if employee["grade"] == "Lead" and employee["career_goal"] is None)
    no_target = client.get(f"/api/employees/{no_goal}/skill-gap").json()
    assert no_target["status"] == "no_target"
    assert client.get(f"/api/employees/{no_goal}/recommendations").json()["recommendations"] == []
    assert client.post(f"/api/employees/{no_goal}/navigator/ask", json={"question": "Что дальше?"}).json()["provider"] == "template"
    assert client.post("/api/employees/E0016/activities/EV_001/actions/enroll").status_code == 422
    gap = client.get("/api/employees/E0001/skill-gap").json()
    assert gap["total_gap_points"] > 0
    for skill in gap["skills"]:
        data.effective_skills["E0001"][skill["skill_id"]] = skill["required_level"]
    ready = client.get("/api/employees/E0001/skill-gap").json()
    assert ready["status"] == "ready" and ready["total_gap_points"] == 0
    assert client.get("/api/employees/E0001/recommendations").json()["recommendations"] == []
    assert client.post("/api/employees/E0001/navigator/ask", json={"question": "Что дальше?"}).json()["summary"].startswith("Все требования")


def test_repeatable_history_can_enroll_again_and_time_budget_is_respected():
    data = load_dataset()
    app.state.dataset = data
    app.state.data_error = None
    client = TestClient(app)
    employee_id = "E0005"
    assert data.activity_status(employee_id, "EV_036") == "completed"
    details = client.get(f"/api/employees/{employee_id}/activities/EV_036").json()
    assert details["eligible"] is True
    path = f"/api/employees/{employee_id}/activities/EV_036"
    assert client.post(f"{path}/actions/enroll").json()["status"] == "enrolled"
    assert client.post(f"{path}/actions/start").json()["status"] == "in_progress"
    assert client.post(f"{path}/complete").status_code == 200
    assert client.post(f"{path}/actions/enroll").json()["status"] == "enrolled"
    answer = client.post("/api/employees/E0001/navigator/ask", json={
        "question": "У меня 2 часа в неделю",
    }).json()
    assert answer["intent"] == "four_hours"
    assert "2 ч в неделю" in answer["summary"]
