"""Career Quest JSON API. Run from the repository root with uvicorn backend.app.main:app."""

from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ml import engine

from .data import Dataset, DatasetError, GRADES, load_dataset
from .models import (
    ActivityActionResponse, ActivityDetailsResponse, ActivityHistoryResponse, CompletionResponse, EmployeeListResponse, EmployeeProfileResponse, ErrorResponse,
    HROverviewResponse, HealthResponse, RecommendationsResponse, RoadmapResponse, SkillGapResponse,
    AIStatusResponse, NavigatorRequest, NavigatorResponse,
)
from .services.ai_provider import get_ai_provider, get_ai_status
from .services.navigator import (
    activity_details, ask_navigator, build_roadmap, calculate_skill_gap, get_employee_profile, recommend_activities,
    simulate_activity_completion,
)


app = FastAPI(title="Career Quest API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.state.dataset = None
app.state.data_error = None


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


@app.exception_handler(APIError)
def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "Invalid request"}})


def _data() -> Dataset:
    if app.state.dataset is None and app.state.data_error is None:
        try:
            app.state.dataset = load_dataset()
        except (DatasetError, ValueError, TypeError, KeyError, AttributeError) as exc:
            app.state.data_error = str(exc)
    if app.state.dataset is None:
        raise APIError(503, "data_unavailable", app.state.data_error or "Dataset unavailable")
    return app.state.dataset


def _employee(data: Dataset, employee_id: str) -> dict:
    if employee_id not in data.employees:
        raise APIError(404, "not_found", f"Employee {employee_id} not found")
    return data.employees[employee_id]


@app.get("/api/health", response_model=HealthResponse, responses={503: {"model": ErrorResponse}})
def health():
    data = _data()
    return {
        "status": "ok", "as_of_date": data.as_of_date,
        "dataset": {
            "employees": len(data.employees), "events": len(data.events),
            "skills": len(data.catalog), "role_profiles": len(data.role_profiles),
        },
    }


@app.get("/api/ai/status", response_model=AIStatusResponse)
def ai_status():
    return get_ai_status()


@app.get("/api/employees", response_model=EmployeeListResponse, responses={503: {"model": ErrorResponse}})
def employees():
    data = _data()
    ordered = sorted(data.employees.values(), key=lambda row: (row["full_name"], row["employee_id"]))
    return {"employees": ordered}


@app.get("/api/employees/{employee_id}", response_model=EmployeeProfileResponse, responses={404: {"model": ErrorResponse}})
def employee_profile(employee_id: str):
    data = _data()
    _employee(data, employee_id)
    with data.lock:
        return get_employee_profile(data, employee_id)


@app.get("/api/employees/{employee_id}/skill-gap", response_model=SkillGapResponse, responses={404: {"model": ErrorResponse}})
def skill_gap(employee_id: str):
    data = _data()
    _employee(data, employee_id)
    with data.lock:
        return calculate_skill_gap(data, employee_id)


@app.get("/api/employees/{employee_id}/recommendations", response_model=RecommendationsResponse, responses={404: {"model": ErrorResponse}})
def recommendations(employee_id: str):
    data = _data()
    _employee(data, employee_id)
    with data.lock:
        return recommend_activities(data, employee_id, get_ai_provider())


@app.get("/api/employees/{employee_id}/roadmap", response_model=RoadmapResponse, responses={404: {"model": ErrorResponse}})
def roadmap(employee_id: str):
    data = _data()
    _employee(data, employee_id)
    with data.lock:
        return build_roadmap(data, employee_id, get_ai_provider())


@app.get("/api/employees/{employee_id}/activities/{event_id}", response_model=ActivityDetailsResponse)
def get_activity(employee_id: str, event_id: str):
    data = _data()
    _employee(data, employee_id)
    if event_id not in data.events:
        raise APIError(404, "not_found", f"Event {event_id} not found")
    with data.lock:
        return activity_details(data, employee_id, event_id, get_ai_provider())


@app.get("/api/employees/{employee_id}/activity-history", response_model=ActivityHistoryResponse)
def activity_history(employee_id: str):
    data = _data()
    _employee(data, employee_id)
    with data.lock:
        historical = [
            {"record_id": row["record_id"], "event_id": row["event_id"],
             "title": data.events[row["event_id"]]["title"], "date": row["date"],
             "status": row["status"], "source": "dataset"}
            for row in data.history_for(employee_id)
        ]
        historical.sort(key=lambda row: (row["date"], row["record_id"]), reverse=True)
        demo = [
            {"record_id": None, "event_id": event_id, "title": data.events[event_id]["title"],
             "date": None, "status": status, "source": "demo"}
            for event_id, status in data.activity_statuses[employee_id].items()
        ]
        return {"employee_id": employee_id, "activities": demo + historical}


@app.post("/api/employees/{employee_id}/activities/{event_id}/actions/{action}", response_model=ActivityActionResponse)
def activity_action(employee_id: str, event_id: str, action: str):
    if action not in {"enroll", "start"}:
        raise APIError(404, "not_found", f"Action {action} not found")
    data = _data()
    employee = _employee(data, employee_id)
    event = data.events.get(event_id)
    if event is None:
        raise APIError(404, "not_found", f"Event {event_id} not found")
    with data.lock:
        status = data.activity_status(employee_id, event_id)
        if status == "completed" and event_id != engine.REPEATABLE_EVENT_ID:
            raise APIError(409, "already_completed", f"Event {event_id} was already completed")
        target = engine.resolve_target(employee, data.role_profiles)
        if not engine.event_is_eligible(event, employee, data.effective_skills[employee_id], target,
                                        data.history_for(employee_id), data.as_of_date,
                                        completed_event_ids=data.session_completions[employee_id]):
            raise APIError(422, "invalid_activity", f"Event {event_id} is not eligible for {employee_id}")
        if action == "start" and status in {"not_started", "completed"}:
            raise APIError(409, "enrollment_required", "Enroll before starting the activity")
        new_status = "enrolled" if action == "enroll" and status in {"not_started", "completed"} else "in_progress" if action == "start" else status
        data.activity_statuses[employee_id][event_id] = new_status
        return {"employee_id": employee_id, "event_id": event_id, "status": new_status}


@app.post("/api/employees/{employee_id}/navigator/ask", response_model=NavigatorResponse)
def navigator_ask(employee_id: str, body: NavigatorRequest):
    data = _data()
    _employee(data, employee_id)
    if body.event_id and body.event_id not in data.events:
        raise APIError(404, "not_found", f"Event {body.event_id} not found")
    provider = get_ai_provider()
    with data.lock:
        answer = ask_navigator(data, employee_id, body.question, body.intent, body.event_id,
                               body.weekly_hours, provider)
    evidence_packet = answer.pop("_evidence_packet")
    return provider.rephrase(answer, body.question, evidence_packet)


@app.post(
    "/api/employees/{employee_id}/activities/{event_id}/complete", response_model=CompletionResponse,
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def complete_activity(employee_id: str, event_id: str):
    data = _data()
    employee = _employee(data, employee_id)
    event = data.events.get(event_id)
    if event is None:
        raise APIError(404, "not_found", f"Event {event_id} not found")
    with data.lock:
        history = data.history_for(employee_id)
        completed = any(row["event_id"] == event_id and row["status"] == "completed" for row in history)
        completed = completed or event_id in data.session_completions[employee_id]
        if event_id != "EV_036" and completed:
            raise APIError(409, "already_completed", f"Event {event_id} was already completed")
        target = engine.resolve_target(employee, data.role_profiles)
        if not engine.event_is_eligible(
            event, employee, data.effective_skills[employee_id], target, history,
            data.as_of_date, completed_event_ids=data.session_completions[employee_id],
        ):
            raise APIError(422, "invalid_activity", f"Event {event_id} is not eligible for {employee_id}")
        return simulate_activity_completion(data, employee_id, event_id, get_ai_provider())


@app.get("/api/hr/overview", response_model=HROverviewResponse, responses={503: {"model": ErrorResponse}})
def hr_overview():
    data = _data()
    with data.lock:
        grade_counts = {grade: 0 for grade in GRADES}
        departments = defaultdict(lambda: {"employee_count": 0, "progress": [], "employees_ready": 0})
        progresses = []
        ready = without_target = explicit_goal = 0
        for employee_id, employee in data.employees.items():
            grade_counts[employee["grade"]] += 1
            explicit_goal += employee.get("career_goal") is not None
            gap = calculate_skill_gap(data, employee_id)
            ready += gap["status"] == "ready"
            without_target += gap["status"] == "no_target"
            exact_progress = (
                100 * gap["total_met_points"] / gap["total_required_points"]
                if gap["total_required_points"] else 100.0
            ) if gap["progress_pct"] is not None else None
            if exact_progress is not None:
                progresses.append(exact_progress)
            bucket = departments[employee["department"]]
            bucket["employee_count"] += 1
            bucket["employees_ready"] += gap["status"] == "ready"
            if exact_progress is not None:
                bucket["progress"].append(exact_progress)
        return {
            "as_of_date": data.as_of_date,
            "employee_count": len(data.employees),
            "employees_with_explicit_goal": explicit_goal,
            "employees_without_explicit_goal": len(data.employees) - explicit_goal,
            "employees_ready": ready,
            "employees_without_target": without_target,
            "average_progress_pct": round(sum(progresses) / len(progresses), 1) if progresses else None,
            "grade_counts": grade_counts,
            "departments": [
                {
                    "department": name,
                    "employee_count": bucket["employee_count"],
                    "average_progress_pct": round(sum(bucket["progress"]) / len(bucket["progress"]), 1) if bucket["progress"] else None,
                    "employees_ready": bucket["employees_ready"],
                }
                for name, bucket in sorted(departments.items())
            ],
        }
