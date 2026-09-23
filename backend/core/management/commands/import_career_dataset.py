import csv
import json
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import ActivityHistory, Employee, LearningEvent, RoleProfile, Skill


class Command(BaseCommand):
    help = "Import Career Quest JSON and CSV files idempotently"

    def add_arguments(self, parser):
        parser.add_argument("--path", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(options["path"])
        required = ["skills.json", "employees.json", "events.json", "activity_history.csv"]
        missing = [name for name in required if not (root / name).is_file()]
        if missing:
            raise CommandError(f"Missing files: {', '.join(missing)}")
        try:
            skills = json.loads((root / "skills.json").read_text(encoding="utf-8"))
            employees = json.loads((root / "employees.json").read_text(encoding="utf-8"))
            events = json.loads((root / "events.json").read_text(encoding="utf-8"))
            with (root / "activity_history.csv").open(encoding="utf-8-sig", newline="") as stream:
                history = list(csv.DictReader(stream))
            skill_ids = {item["skill_id"] for item in skills["skills"]}
            event_ids = {item["event_id"] for item in events["events"]}
            employee_ids = {item["employee_id"] for item in employees["employees"]}
            if len(skill_ids) != len(skills["skills"]) or len(event_ids) != len(events["events"]) or len(employee_ids) != len(employees["employees"]):
                raise ValueError("Duplicate external IDs")
            for profile in skills["role_profiles"]:
                if not set(profile["required_skills"]) <= skill_ids or not set(profile["critical_skills"]) <= skill_ids:
                    raise ValueError("Role profile references an unknown skill")
            for event in events["events"]:
                if any(gain["skill_id"] not in skill_ids for gain in event["develops_skills"]) or not set(event["prerequisites"]) <= skill_ids:
                    raise ValueError(f"Event {event['event_id']} references an unknown skill")
            for employee in employees["employees"]:
                if not set(employee["skills"]) <= skill_ids:
                    raise ValueError(f"Employee {employee['employee_id']} references an unknown skill")
            allowed_status = {"completed", "in_progress", "dropped", "declined", "no_show", "overdue"}
            for row in history:
                if row["employee_id"] not in employee_ids or row["event_id"] not in event_ids or row["status"] not in allowed_status:
                    raise ValueError(f"Invalid history row {row['record_id']}")
                if not 0 <= int(row["completion_pct"]) <= 100:
                    raise ValueError(f"Invalid completion percentage {row['record_id']}")
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError(f"Invalid dataset: {exc}") from exc

        for item in skills["skills"]:
            Skill.objects.update_or_create(external_id=item["skill_id"], defaults={
                "name": item["name"], "category": item.get("category", ""), "metadata": item})
        for item in skills["role_profiles"]:
            RoleProfile.objects.update_or_create(role=item["role"], grade=item["grade"], defaults={
                "required_skills": item["required_skills"], "critical_skills": item["critical_skills"]})
        for item in events["events"]:
            LearningEvent.objects.update_or_create(external_id=item["event_id"], defaults={
                "title": item["title"], "description": item.get("description", ""),
                "duration_hours": item.get("duration_hours", 0), "format": item.get("format", ""),
                "mandatory": item.get("mandatory", False),
                "repeatable": item.get("repeatable", item["event_id"] == "EV_036"),
                "target_roles": item.get("target_roles", []), "target_grades": item.get("target_grades", []),
                "develops_skills": item.get("develops_skills", []),
                "prerequisites": item.get("prerequisites", {}), "metadata": item})
        for item in employees["employees"]:
            Employee.objects.update_or_create(external_id=item["employee_id"], defaults={
                "full_name": item["full_name"], "role": item["role"], "grade": item["grade"],
                "department": item.get("department", ""),
                "last_review_date": date.fromisoformat(item["last_review_date"]),
                "baseline_skills": item["skills"], "career_goal": item.get("career_goal"),
                "metadata": {k: v for k, v in item.items() if k not in ("skills", "career_goal")}})
        employee_map = Employee.objects.in_bulk(field_name="external_id")
        event_map = LearningEvent.objects.in_bulk(field_name="external_id")
        for row in history:
            ActivityHistory.objects.update_or_create(external_id=row["record_id"], defaults={
                "employee": employee_map[row["employee_id"]], "event": event_map[row["event_id"]],
                "date": date.fromisoformat(row["date"]), "status": row["status"],
                "completion_pct": int(row["completion_pct"]),
                "metadata": {k: v for k, v in row.items() if k not in ("record_id", "employee_id", "event_id", "date", "status", "completion_pct")}})
        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(skill_ids)} skills, {len(skills['role_profiles'])} profiles, "
            f"{len(event_ids)} events, {len(employee_ids)} employees, {len(history)} activities"))
