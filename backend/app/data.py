"""Load and validate the source dataset once; session changes stay in memory."""

import csv
import json
import os
from datetime import date
from pathlib import Path
from threading import RLock

from .models import EmployeeProfile


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "datasets" / "career_quest"
GRADES = ("Junior", "Middle", "Senior", "Lead")
TERMINAL_STATUSES = {"completed", "dropped", "no_show", "declined", "overdue"}
STATUSES = TERMINAL_STATUSES | {"in_progress"}


class DatasetError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DatasetError(message)


def _date(value: str, context: str) -> date:
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise DatasetError(f"Invalid date at {context}: {value!r}") from exc


def _unique(records: list[dict], key: str, context: str) -> dict[str, dict]:
    result = {}
    for row in records:
        identifier = row.get(key)
        _require(isinstance(identifier, str) and bool(identifier), f"Missing {key} in {context}")
        _require(identifier not in result, f"Duplicate {key} {identifier} in {context}")
        result[identifier] = row
    return result


def load_dataset(data_dir: Path | None = None) -> "Dataset":
    root = Path(data_dir or os.getenv("CAREER_QUEST_DATA_DIR") or DEFAULT_DATA_DIR).resolve()
    try:
        with (root / "skills.json").open(encoding="utf-8") as stream:
            skills_doc = json.load(stream)
        with (root / "employees.json").open(encoding="utf-8") as stream:
            employees_doc = json.load(stream)
        with (root / "events.json").open(encoding="utf-8") as stream:
            events_doc = json.load(stream)
        with (root / "activity_history.csv").open(encoding="utf-8-sig", newline="") as stream:
            history = list(csv.DictReader(stream))
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        raise DatasetError(f"Cannot load Career Quest dataset from {root}: {exc}") from exc

    for label, doc in (("skills", skills_doc), ("employees", employees_doc), ("events", events_doc)):
        _require(isinstance(doc, dict) and isinstance(doc.get("meta"), dict), f"Invalid {label}.json structure")
    dates = [doc["meta"].get("as_of_date") for doc in (skills_doc, employees_doc, events_doc)]
    _require(len(set(dates)) == 1, "Dataset snapshot dates disagree")
    as_of_date = dates[0]
    _date(as_of_date, "meta.as_of_date")

    catalog = skills_doc.get("skills")
    role_profiles = skills_doc.get("role_profiles")
    employees = employees_doc.get("employees")
    events = events_doc.get("events")
    for label, rows in (("skills", catalog), ("role_profiles", role_profiles), ("employees", employees), ("events", events)):
        _require(isinstance(rows, list), f"Expected array at {label}")
    skills_by_id = _unique(catalog, "skill_id", "skills")
    employees_by_id = _unique(employees, "employee_id", "employees")
    events_by_id = _unique(events, "event_id", "events")
    _unique(history, "record_id", "history")

    for skill in catalog:
        skill_id = skill["skill_id"]
        _require(skill.get("type") in {"hard", "soft"}, f"Invalid skill type for {skill_id}")
        for field in ("name", "category", "description"):
            _require(isinstance(skill.get(field), str) and skill[field], f"Missing {field} for {skill_id}")

    profiles_by_key = {}
    for profile in role_profiles:
        key = (profile.get("role"), profile.get("grade"))
        _require(key[1] in GRADES and key not in profiles_by_key, f"Invalid or duplicate role profile {key}")
        required = profile.get("required_skills")
        critical = profile.get("critical_skills")
        _require(isinstance(required, dict) and isinstance(critical, list), f"Invalid requirements for {key}")
        for skill_id, level in required.items():
            _require(skill_id in skills_by_id and type(level) is int and 0 <= level <= 5, f"Invalid required skill {skill_id} for {key}")
        _require(set(critical).issubset(required), f"Unknown critical skill for {key}")
        profiles_by_key[key] = profile

    for employee in employees:
        employee_id = employee["employee_id"]
        try:
            EmployeeProfile.model_validate(employee)
        except Exception as exc:
            raise DatasetError(f"Invalid employee {employee_id}: {exc}") from exc
        _require((employee["role"], employee["grade"]) in profiles_by_key, f"Unknown role/grade for {employee_id}")
        goal = employee.get("career_goal")
        if goal is not None:
            _require((goal["target_role"], goal["target_grade"]) in profiles_by_key, f"Unknown goal for {employee_id}")
        _require(employee.get("manager_id") is None or employee["manager_id"] in employees_by_id, f"Unknown manager for {employee_id}")
        _date(employee["hire_date"], f"{employee_id}.hire_date")
        _date(employee["last_review_date"], f"{employee_id}.last_review_date")
        _require(employee["tenure_months"] >= 0, f"Negative tenure for {employee_id}")
        for skill_id, level in employee["skills"].items():
            _require(skill_id in skills_by_id and type(level) is int and 0 <= level <= 5, f"Invalid skill {skill_id} for {employee_id}")

    for event in events:
        event_id = event["event_id"]
        for field in ("title", "description", "type"):
            _require(isinstance(event.get(field), str) and event[field], f"Missing {field} for {event_id}")
        _require(type(event.get("mandatory")) is bool, f"Invalid mandatory flag for {event_id}")
        _require(event.get("format") in {"online", "offline", "self_paced"}, f"Invalid format for {event_id}")
        _require(isinstance(event.get("duration_hours"), (int, float)) and not isinstance(event["duration_hours"], bool) and event["duration_hours"] > 0, f"Invalid duration for {event_id}")
        _require(isinstance(event.get("target_roles"), list) and isinstance(event.get("target_grades"), list), f"Invalid audience for {event_id}")
        _require(set(event["target_roles"]).issubset({profile["role"] for profile in role_profiles}), f"Unknown target role for {event_id}")
        _require(set(event["target_grades"]).issubset(GRADES), f"Invalid grade for {event_id}")
        _require(isinstance(event.get("prerequisites"), dict) and isinstance(event.get("develops_skills"), list), f"Invalid skills for {event_id}")
        for skill_id, level in event["prerequisites"].items():
            _require(skill_id in skills_by_id and type(level) is int and 0 <= level <= 5, f"Invalid prerequisite {skill_id} for {event_id}")
        developed_ids = [gain.get("skill_id") for gain in event["develops_skills"]]
        _require(len(developed_ids) == len(set(developed_ids)), f"Duplicate developed skill for {event_id}")
        for gain in event["develops_skills"]:
            _require(gain.get("skill_id") in skills_by_id and type(gain.get("gain")) is int and gain["gain"] >= 0, f"Invalid gain for {event_id}")
            _require(type(gain.get("max_level")) is int and 0 <= gain["max_level"] <= 5, f"Invalid max_level for {event_id}")
        sessions = event.get("upcoming_sessions")
        _require(isinstance(sessions, list), f"Invalid sessions for {event_id}")
        for value in sessions:
            _date(value, f"{event_id}.upcoming_sessions")

    for row in history:
        record_id = row["record_id"]
        _require(row.get("employee_id") in employees_by_id and row.get("event_id") in events_by_id, f"Unknown history relation in {record_id}")
        _date(row.get("date"), f"{record_id}.date")
        if row.get("due_date"):
            _date(row["due_date"], f"{record_id}.due_date")
        _require(row.get("status") in STATUSES, f"Invalid history status in {record_id}")
        for name, low, high in (("completion_pct", 0, 100), ("score", 0, 100), ("feedback_rating", 1, 5)):
            value = row.get(name)
            if value not in (None, ""):
                _require(value.isdecimal() and low <= int(value) <= high, f"Invalid {name} in {record_id}")
        _require(row.get("assigned_by") in {"self", "manager", "hr"}, f"Invalid assigned_by in {record_id}")

    return Dataset(as_of_date, catalog, role_profiles, employees_by_id, events_by_id, history)


class Dataset:
    def __init__(self, as_of_date, catalog, role_profiles, employees, events, history):
        self.as_of_date = as_of_date
        self.catalog = catalog
        self.role_profiles = role_profiles
        self.employees = employees
        self.events = events
        self.history = history
        self.effective_skills = {employee_id: dict(employee["skills"]) for employee_id, employee in employees.items()}
        self.session_completions: dict[str, set[str]] = {employee_id: set() for employee_id in employees}
        self.lock = RLock()

    def history_for(self, employee_id: str) -> list[dict]:
        return [row for row in self.history if row["employee_id"] == employee_id]
