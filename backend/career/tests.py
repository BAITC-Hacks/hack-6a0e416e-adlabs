from __future__ import annotations

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from career.models import (
    ActivityHistory,
    Employee,
    EmployeeQuest,
    LearningEvent,
    RoleProfile,
    Skill,
    XPTransaction,
)
from career.services.engine import effective_skills, recommendations, readiness, target_profile


class CareerQuestIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("import_career_dataset", verbosity=0)

    def setUp(self) -> None:
        self.client = APIClient()

    @staticmethod
    def employee_headers(employee_id: str = "E0001") -> dict[str, str]:
        return {
            "HTTP_X_DEMO_ROLE": "employee",
            "HTTP_X_EMPLOYEE_ID": employee_id,
        }

    def test_import_is_idempotent_and_complete(self) -> None:
        expected = {
            "employees": Employee.objects.count(),
            "skills": Skill.objects.count(),
            "profiles": RoleProfile.objects.count(),
            "events": LearningEvent.objects.count(),
            "history": ActivityHistory.objects.count(),
        }
        self.assertEqual(
            expected,
            {"employees": 200, "skills": 60, "profiles": 32, "events": 40, "history": 2743},
        )

        call_command("import_career_dataset", verbosity=0)

        self.assertEqual(Employee.objects.count(), expected["employees"])
        self.assertEqual(Skill.objects.count(), expected["skills"])
        self.assertEqual(RoleProfile.objects.count(), expected["profiles"])
        self.assertEqual(LearningEvent.objects.count(), expected["events"])
        self.assertEqual(ActivityHistory.objects.count(), expected["history"])

    def test_effective_skills_and_weighted_readiness_follow_spec(self) -> None:
        employee = Employee.objects.get(pk="E0001")
        expected = {skill_id: int(level) for skill_id, level in employee.skills.items()}
        completions = employee.activities.filter(
            status="completed", date__gt=employee.last_review_date
        ).select_related("event")
        for completion in completions:
            for gain in completion.event.develops_skills:
                skill_id = gain["skill_id"]
                expected[skill_id] = min(
                    expected.get(skill_id, 0) + int(gain["gain"]),
                    int(gain["max_level"]),
                )

        actual = effective_skills(employee)
        self.assertEqual(actual, expected)

        profile = target_profile(employee)
        self.assertIsNotNone(profile)
        critical = set(profile.critical_skills)
        weighted_score = 0.0
        total_weight = 0.0
        for skill_id, required in profile.required_skills.items():
            weight = 2.0 if skill_id in critical else 1.0
            weighted_score += min(actual.get(skill_id, 0) / int(required), 1.0) * weight
            total_weight += weight
        self.assertEqual(readiness(employee), round(weighted_score / total_weight * 100))

    def test_recommendations_are_eligible_explainable_and_deterministic(self) -> None:
        employee = Employee.objects.get(pk="E0001")
        first = recommendations(employee)
        second = recommendations(employee)

        self.assertGreaterEqual(len(first), 1)
        self.assertLessEqual(len(first), 3)
        self.assertEqual(
            [item["event_id"] for item in first],
            [item["event_id"] for item in second],
        )

        completed = set(
            employee.activities.filter(status="completed").values_list("event_id", flat=True)
        )
        active = set(
            employee.activities.filter(status="in_progress").values_list("event_id", flat=True)
        )
        goal = employee.career_goal
        for item in first:
            self.assertFalse(item["mandatory"])
            self.assertNotIn(item["event_id"], active)
            if item["event_id"] != "EV_036":
                self.assertNotIn(item["event_id"], completed)
            self.assertEqual({reason["group"] for reason in item["reasons"]}, {"goal", "skills", "history"})
            event = LearningEvent.objects.get(pk=item["event_id"])
            self.assertIn(goal["target_role"], event.target_roles)
            self.assertIn(goal["target_grade"], event.target_grades)
            self.assertLessEqual(len(item["quest_chain"]), 3)

    def test_employee_and_hr_scopes_are_separated(self) -> None:
        missing_scope = self.client.get("/api/v1/employees/E0001/dashboard/")
        self.assertEqual(missing_scope.status_code, 403)

        denied = self.client.get(
            "/api/v1/employees/E0002/dashboard/", **self.employee_headers("E0001")
        )
        self.assertEqual(denied.status_code, 403)
        self.assertIn("error", denied.json())

        denied_hr = self.client.get("/api/v1/hr/overview/", **self.employee_headers())
        self.assertEqual(denied_hr.status_code, 403)
        denied_hr_profiles = self.client.get("/api/v1/employees/", HTTP_X_DEMO_ROLE="hr")
        self.assertEqual(denied_hr_profiles.status_code, 403)

        allowed_hr = self.client.get("/api/v1/hr/overview/", HTTP_X_DEMO_ROLE="hr")
        self.assertEqual(allowed_hr.status_code, 200)
        self.assertEqual(allowed_hr.json()["totals"]["employees"], 200)

    def test_quest_actions_are_atomic_idempotent_and_guarded(self) -> None:
        payload = {"employee_id": "E0001"}
        headers = self.employee_headers()

        rejected_locked = self.client.post(
            "/api/v1/quests/EV_006/complete/", payload, format="json", **headers
        )
        self.assertEqual(rejected_locked.status_code, 400)
        self.assertIn("prerequisites", rejected_locked.json()["error"]["details"])

        employee = Employee.objects.get(pk="E0001")
        goal = employee.career_goal
        ineligible = next(
            event
            for event in LearningEvent.objects.filter(mandatory=False)
            if goal["target_role"] not in event.target_roles
            or goal["target_grade"] not in event.target_grades
        )
        rejected_goal = self.client.post(
            f"/api/v1/quests/{ineligible.external_id}/start/",
            payload,
            format="json",
            **headers,
        )
        self.assertEqual(rejected_goal.status_code, 400)

        first_start = self.client.post("/api/v1/quests/EV_005/start/", payload, format="json", **headers)
        second_start = self.client.post("/api/v1/quests/EV_005/start/", payload, format="json", **headers)
        self.assertEqual(first_start.status_code, 201)
        self.assertEqual(second_start.status_code, 200)
        self.assertTrue(second_start.json()["idempotent"])

        first_complete = self.client.post(
            "/api/v1/quests/EV_005/complete/", payload, format="json", **headers
        )
        second_complete = self.client.post(
            "/api/v1/quests/EV_005/complete/", payload, format="json", **headers
        )
        self.assertEqual(first_complete.status_code, 200)
        self.assertFalse(first_complete.json()["idempotent"])
        self.assertTrue(second_complete.json()["idempotent"])
        self.assertEqual(
            first_complete.json()["dashboard"]["progress"]["xp"],
            second_complete.json()["dashboard"]["progress"]["xp"],
        )
        self.assertEqual(EmployeeQuest.objects.filter(employee_id="E0001", event_id="EV_005").count(), 1)
        self.assertEqual(
            ActivityHistory.objects.filter(record_id="DEMO-E0001-EV_005").count(), 1
        )
        self.assertLessEqual(
            XPTransaction.objects.filter(employee_id="E0001", event_id="EV_005").count(), 1
        )

        mandatory = LearningEvent.objects.filter(mandatory=True).first()
        self.assertIsNotNone(mandatory)
        rejected_mandatory = self.client.post(
            f"/api/v1/quests/{mandatory.external_id}/complete/", payload, format="json", **headers
        )
        self.assertEqual(rejected_mandatory.status_code, 400)

    def test_repeatable_quest_supports_new_cycles_but_not_duplicate_retries(self) -> None:
        employee_id = "E0147"
        payload = {"employee_id": employee_id}
        headers = self.employee_headers(employee_id)

        first_start = self.client.post(
            "/api/v1/quests/EV_036/start/", payload, format="json", **headers
        )
        first_complete = self.client.post(
            "/api/v1/quests/EV_036/complete/", payload, format="json", **headers
        )
        retry_complete = self.client.post(
            "/api/v1/quests/EV_036/complete/", payload, format="json", **headers
        )
        self.assertEqual(first_start.status_code, 201)
        self.assertEqual(first_complete.status_code, 200)
        self.assertTrue(retry_complete.json()["idempotent"])
        self.assertEqual(
            first_complete.json()["dashboard"]["progress"]["xp"],
            retry_complete.json()["dashboard"]["progress"]["xp"],
        )

        restarted = self.client.post(
            "/api/v1/quests/EV_036/start/", payload, format="json", **headers
        )
        second_complete = self.client.post(
            "/api/v1/quests/EV_036/complete/", payload, format="json", **headers
        )
        self.assertEqual(restarted.status_code, 201)
        self.assertTrue(restarted.json()["restarted"])
        self.assertEqual(second_complete.status_code, 200)
        self.assertEqual(
            second_complete.json()["dashboard"]["progress"]["xp"],
            first_complete.json()["dashboard"]["progress"]["xp"] + 200,
        )
        self.assertEqual(
            ActivityHistory.objects.filter(
                employee_id=employee_id,
                event_id="EV_036",
                record_id__startswith=f"DEMO-{employee_id}-EV_036-",
            ).count(),
            2,
        )
