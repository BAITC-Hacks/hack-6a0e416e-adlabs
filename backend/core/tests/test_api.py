from datetime import date, timedelta
import json
import pytest
from django.core.management import call_command
from django.test import override_settings
from core.models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, XPTransaction
from core.services import career_snapshot


@pytest.mark.django_db
def test_import_is_idempotent():
    path = "../datasets/career_quest"
    call_command("import_career_dataset", path=path)
    counts = (Employee.objects.count(), LearningEvent.objects.count(), ActivityHistory.objects.count())
    call_command("import_career_dataset", path=path)
    assert counts == (Employee.objects.count(), LearningEvent.objects.count(), ActivityHistory.objects.count())
    assert counts == (200, 40, 2743)


@pytest.mark.django_db
@override_settings(DEMO_MODE=True, ALLOWED_HOSTS=["testserver"])
def test_quest_complete_once_and_recalculates(client):
    RoleProfile.objects.create(role="Engineer", grade="Middle", required_skills={"A": 2}, critical_skills=["A"])
    employee = Employee.objects.create(external_id="E1", full_name="Test", role="Engineer", grade="Junior",
        last_review_date=date.today()-timedelta(days=2), baseline_skills={"A": 0},
        career_goal={"target_role": "Engineer", "target_grade": "Middle"})
    event = LearningEvent.objects.create(external_id="EV1", title="Learn A", develops_skills=[
        {"skill_id":"A","gain":1,"max_level":5}], duration_hours=1)
    url = "/api/v1/quests/EV1/"
    data = json.dumps({"employee_id": "E1"})
    assert client.post(url+"start/", data, content_type="application/json").status_code == 200
    result = client.post(url+"complete/", data, content_type="application/json")
    assert result.status_code == 200
    assert result.json()["readiness_after"] > result.json()["readiness_before"]
    assert client.post(url+"complete/", data, content_type="application/json").status_code == 400
    assert XPTransaction.objects.filter(employee=employee).count() == 1
    assert ActivityHistory.objects.filter(employee=employee, event=event).count() == 1
    assert EmployeeQuest.objects.get(employee=employee, event=event).xp_awarded == 300


@pytest.mark.django_db
@override_settings(DEMO_MODE=True, ALLOWED_HOSTS=["testserver"])
def test_imported_active_disappears_after_completion(client):
    employee = Employee.objects.create(external_id="E2", full_name="Test", role="Engineer", grade="Junior",
        last_review_date=date.today()-timedelta(days=2), baseline_skills={})
    event = LearningEvent.objects.create(external_id="EV2", title="Learning")
    ActivityHistory.objects.create(external_id="R1", employee=employee, event=event,
                                   date=date.today(), status="in_progress")
    assert len(career_snapshot(employee)["active_quests"]) == 1
    response = client.post("/api/v1/quests/EV2/complete/", json.dumps({"employee_id": "E2"}),
                           content_type="application/json")
    assert response.status_code == 200
    snap = career_snapshot(employee)
    assert snap["active_quests"] == []
    assert snap["completed_quests"][0]["event_id"] == "EV2"


@pytest.mark.django_db
@override_settings(DEMO_MODE=True, ALLOWED_HOSTS=["testserver"])
def test_full_prerequisite_chain_awards_bonus_once(client):
    RoleProfile.objects.create(role="Engineer", grade="Middle", required_skills={"A": 1, "B": 1})
    employee = Employee.objects.create(external_id="E3", full_name="Test", role="Engineer", grade="Junior",
        last_review_date=date.today()-timedelta(days=2), baseline_skills={},
        career_goal={"target_role": "Engineer", "target_grade": "Middle"})
    LearningEvent.objects.create(external_id="BASE", title="Base", develops_skills=[
        {"skill_id": "A", "gain": 1, "max_level": 5}])
    LearningEvent.objects.create(external_id="TARGET", title="Target", develops_skills=[
        {"skill_id": "B", "gain": 1, "max_level": 5}], prerequisites={"A": 1})
    data = json.dumps({"employee_id": "E3"})
    for event_id in ("BASE", "TARGET"):
        assert client.post(f"/api/v1/quests/{event_id}/start/", data, content_type="application/json").status_code == 200
        response = client.post(f"/api/v1/quests/{event_id}/complete/", data, content_type="application/json")
        assert response.status_code == 200
    assert response.json()["xp_awarded"] == 500
    assert "QUEST_MASTER" in career_snapshot(employee)["achievements"]
    assert employee.xp_transactions.count() == 2
