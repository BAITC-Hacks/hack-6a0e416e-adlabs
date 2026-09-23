from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from career.models import ActivityHistory, Employee, LearningEvent, RoleProfile, Skill


REQUIRED_FILES = ("employees.json", "skills.json", "events.json", "activity_history.csv")


def parse_optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def parse_optional_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


class Command(BaseCommand):
    help = "Import the Career Quest JSON/CSV dataset idempotently."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--path", type=Path, default=settings.CAREER_DATASET_PATH)
        parser.add_argument(
            "--reset-demo-state",
            action="store_true",
            help="Delete demo quests and XP transactions before importing source data.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        source: Path = options["path"].expanduser().resolve()
        missing = [name for name in REQUIRED_FILES if not (source / name).is_file()]
        if missing:
            raise CommandError(f"Dataset is incomplete at {source}: missing {', '.join(missing)}")

        with (source / "skills.json").open(encoding="utf-8") as stream:
            skill_document = json.load(stream)
        with (source / "employees.json").open(encoding="utf-8") as stream:
            employee_document = json.load(stream)
        with (source / "events.json").open(encoding="utf-8") as stream:
            event_document = json.load(stream)
        with (source / "activity_history.csv").open(encoding="utf-8", newline="") as stream:
            history_rows = list(csv.DictReader(stream))

        expected_counts = {
            "skills": len(skill_document.get("skills", [])),
            "role_profiles": len(skill_document.get("role_profiles", [])),
            "employees": len(employee_document.get("employees", [])),
            "events": len(event_document.get("events", [])),
            "history": len(history_rows),
        }
        if not all(expected_counts.values()):
            raise CommandError(f"Dataset contains an empty collection: {expected_counts}")

        with transaction.atomic():
            if options["reset_demo_state"]:
                from career.models import EmployeeQuest, XPTransaction

                EmployeeQuest.objects.all().delete()
                XPTransaction.objects.all().delete()
                ActivityHistory.objects.filter(record_id__startswith="DEMO-").delete()

            for item in skill_document["skills"]:
                Skill.objects.update_or_create(
                    external_id=item["skill_id"],
                    defaults={
                        "name": item["name"],
                        "type": item["type"],
                        "category": item["category"],
                        "description": item.get("description", ""),
                    },
                )

            for item in skill_document["role_profiles"]:
                RoleProfile.objects.update_or_create(
                    role=item["role"],
                    grade=item["grade"],
                    defaults={
                        "required_skills": item["required_skills"],
                        "critical_skills": item["critical_skills"],
                    },
                )

            employee_items = employee_document["employees"]
            employee_ids = {item["employee_id"] for item in employee_items}
            for item in employee_items:
                Employee.objects.update_or_create(
                    external_id=item["employee_id"],
                    defaults={
                        "full_name": item["full_name"],
                        "department": item["department"],
                        "role": item["role"],
                        "grade": item["grade"],
                        "hire_date": date.fromisoformat(item["hire_date"]),
                        "tenure_months": item["tenure_months"],
                        "work_format": item["work_format"],
                        "preferred_language": item["preferred_language"],
                        "career_goal": item.get("career_goal"),
                        "skills": item["skills"],
                        "last_review_date": date.fromisoformat(item["last_review_date"]),
                    },
                )

            for item in employee_items:
                manager_id = item.get("manager_id")
                if manager_id and manager_id not in employee_ids:
                    raise CommandError(f"Unknown manager {manager_id} for {item['employee_id']}")
                Employee.objects.filter(pk=item["employee_id"]).update(manager_id=manager_id or None)

            for item in event_document["events"]:
                LearningEvent.objects.update_or_create(
                    external_id=item["event_id"],
                    defaults={
                        "title": item["title"],
                        "description": item.get("description", ""),
                        "type": item["type"],
                        "format": item["format"],
                        "duration_hours": item["duration_hours"],
                        "mandatory": item["mandatory"],
                        "target_roles": item["target_roles"],
                        "target_grades": item["target_grades"],
                        "develops_skills": item["develops_skills"],
                        "prerequisites": item["prerequisites"],
                        "upcoming_sessions": item["upcoming_sessions"],
                    },
                )

            known_employees = set(Employee.objects.values_list("external_id", flat=True))
            known_events = set(LearningEvent.objects.values_list("external_id", flat=True))
            for row in history_rows:
                if row["employee_id"] not in known_employees:
                    raise CommandError(f"Unknown employee in history: {row['employee_id']}")
                if row["event_id"] not in known_events:
                    raise CommandError(f"Unknown event in history: {row['event_id']}")
                ActivityHistory.objects.update_or_create(
                    record_id=row["record_id"],
                    defaults={
                        "employee_id": row["employee_id"],
                        "event_id": row["event_id"],
                        "date": date.fromisoformat(row["date"]),
                        "due_date": parse_optional_date(row.get("due_date")),
                        "status": row["status"],
                        "completion_pct": int(row["completion_pct"]),
                        "score": parse_optional_int(row.get("score")),
                        "feedback_rating": parse_optional_int(row.get("feedback_rating")),
                        "assigned_by": row["assigned_by"],
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Imported Career Quest dataset: "
                + ", ".join(f"{name}={count}" for name, count in expected_counts.items())
            )
        )
