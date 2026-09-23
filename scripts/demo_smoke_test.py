"""Isolated API golden-path smoke test. Run from the repository root."""

from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["AI_PROVIDER"] = "template"

from fastapi.testclient import TestClient  # noqa: E402
from backend.app.data import load_dataset  # noqa: E402
from backend.app.main import app  # noqa: E402


def main() -> None:
    data = load_dataset()
    skill_ids = {skill["skill_id"] for skill in data.catalog}
    app.state.dataset = data
    app.state.data_error = None
    client = TestClient(app)
    employee_id = "E0100"
    base = f"/api/employees/{employee_id}"

    def get(path: str) -> dict:
        response = client.get(path)
        assert response.status_code == 200, (path, response.status_code, response.text)
        return response.json()

    health = get("/api/health")
    assert health["status"] == "ok" and health["dataset"]["employees"] == 200
    profile = get(base)
    assert profile["employee"]["employee_id"] == employee_id
    assert profile["target"]["grade"] == "Middle"
    before = get(f"{base}/skill-gap")
    assert before["critical_gap_points"] > 0
    recs = get(f"{base}/recommendations")["recommendations"]
    assert len(recs) == 3
    assert all(recs[i]["score"] >= recs[i + 1]["score"] for i in range(2))
    roadmap = get(f"{base}/roadmap")
    assert roadmap["steps"] and roadmap["steps"][0]["recommendation"]["event_id"] == recs[0]["event_id"]
    event_id = recs[0]["event_id"]
    answer = client.post(f"{base}/navigator/ask", json={"question": "Почему эта активность лучше второй?"})
    assert answer.status_code == 200, answer.text
    answer = answer.json()
    assert {employee_id, recs[0]["event_id"], recs[1]["event_id"]} <= set(answer["evidence_ids"])
    assert all(answer[key] for key in ("summary", "profile_facts", "reason", "expected_effect", "limitation", "next_step"))
    for rec in recs:
        assert rec["event_id"] in data.events
        assert all(gain["skill_id"] in skill_ids for gain in rec["matched_skill_gains"])
    completed = client.post(f"{base}/activities/{event_id}/complete")
    assert completed.status_code == 200, completed.text
    result = completed.json()
    assert result["skill_gap"]["progress_pct"] > before["progress_pct"]
    assert result["skill_gap"]["progress_pct"] == recs[0]["projected_impact"]["progress_after_pct"]
    assert get(f"{base}/skill-gap")["progress_pct"] == result["skill_gap"]["progress_pct"]
    assert all(gain["skill_id"] in skill_ids for gain in result["applied_skill_gains"])
    print(f"PASS {employee_id}: {before['progress_pct']}% -> {result['skill_gap']['progress_pct']}%, {event_id}")


if __name__ == "__main__":
    main()
