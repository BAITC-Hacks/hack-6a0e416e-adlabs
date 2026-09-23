"""API contract smoke tests against the supplied synthetic dataset."""

import json
import shutil

from fastapi.testclient import TestClient

from backend.app.data import DEFAULT_DATA_DIR, DatasetError, load_dataset
from backend.app.main import app
from backend.app.services.ai_provider import TemplateAIProvider


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
