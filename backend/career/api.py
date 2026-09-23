from __future__ import annotations

from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler

from .models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, XPTransaction
from .serializers import CareerGoalSerializer, CoachRequestSerializer, QuestActionSerializer
from .services.coach import answer as coach_answer
from .services.engine import (
    career_payload,
    dashboard,
    effective_skills,
    hr_overview,
    quest_groups,
    recommendations,
    serialize_employee,
    skill_gap,
    skills_payload,
)


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    if isinstance(response.data, dict) and "detail" in response.data:
        message = str(response.data["detail"])
    else:
        message = "Request validation failed"
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "request_error").upper(),
            "message": message,
            "details": response.data,
        }
    }
    return response


def demo_role(request) -> str:
    return request.headers.get("X-Demo-Role", "employee").strip().lower()


def enforce_employee_scope(request, employee_id: str) -> None:
    if demo_role(request) == "hr":
        raise PermissionDenied("HR role can use aggregate HR endpoints only.")
    selected = request.headers.get("X-Employee-ID")
    if not selected:
        raise PermissionDenied("X-Employee-ID is required for employee-scoped endpoints.")
    if selected != employee_id:
        raise PermissionDenied("Employee role cannot access another employee profile.")


def scoped_employee(request, employee_id: str) -> Employee:
    enforce_employee_scope(request, employee_id)
    return get_object_or_404(Employee, pk=employee_id)


def validate_quest_eligibility(employee: Employee, event: LearningEvent) -> None:
    if event.mandatory:
        raise ValidationError({"event_id": "Mandatory events are not Career Quest recommendations."})
    goal = employee.career_goal
    if not goal:
        raise ValidationError({"career_goal": "Choose a career goal before starting a quest."})
    if goal.get("target_role") not in event.target_roles or goal.get("target_grade") not in event.target_grades:
        raise ValidationError({"event_id": "This event does not match the current career goal."})
    values = effective_skills(employee)
    unmet = {
        skill_id: required
        for skill_id, required in event.prerequisites.items()
        if values.get(skill_id, 0) < int(required)
    }
    if unmet:
        raise ValidationError({"prerequisites": unmet})


class HealthView(APIView):
    def get(self, request):
        return Response(
            {
                "status": "ok",
                "snapshot_date": settings.CAREER_SNAPSHOT_DATE.isoformat(),
                "counts": {
                    "employees": Employee.objects.count(),
                    "events": LearningEvent.objects.count(),
                },
            }
        )


class EmployeeListView(APIView):
    def get(self, request):
        if demo_role(request) == "hr":
            raise PermissionDenied("HR role can use aggregate HR endpoints only.")
        query = request.query_params.get("q", "").strip()
        try:
            limit = min(max(int(request.query_params.get("limit", 60)), 1), 200)
        except ValueError as exc:
            raise ValidationError({"limit": "Must be an integer."}) from exc
        employees = Employee.objects.all()
        if query:
            employees = employees.filter(
                Q(full_name__icontains=query)
                | Q(external_id__icontains=query)
                | Q(role__icontains=query)
                | Q(department__icontains=query)
            )
        payload = [serialize_employee(employee) for employee in employees[:limit]]
        return Response({"results": payload, "count": employees.count()})


class EmployeeDetailView(APIView):
    def get(self, request, employee_id: str):
        employee = scoped_employee(request, employee_id)
        return Response(serialize_employee(employee))


class DashboardView(APIView):
    def get(self, request, employee_id: str):
        return Response(dashboard(scoped_employee(request, employee_id)))


class SkillsView(APIView):
    def get(self, request, employee_id: str):
        return Response(skills_payload(scoped_employee(request, employee_id)))


class CareerView(APIView):
    def get(self, request, employee_id: str):
        return Response(career_payload(scoped_employee(request, employee_id)))


class RecommendationView(APIView):
    def get(self, request, employee_id: str):
        employee = scoped_employee(request, employee_id)
        return Response({"employee_id": employee.external_id, "results": recommendations(employee)})


class QuestListView(APIView):
    def get(self, request, employee_id: str):
        employee = scoped_employee(request, employee_id)
        return Response({"employee_id": employee.external_id, **quest_groups(employee)})


class RoleProfileListView(APIView):
    def get(self, request):
        profiles = RoleProfile.objects.values("role", "grade").order_by("role", "id")
        return Response({"results": list(profiles)})


class CareerGoalView(APIView):
    def post(self, request, employee_id: str):
        employee = scoped_employee(request, employee_id)
        serializer = CareerGoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        goal = serializer.validated_data
        if not RoleProfile.objects.filter(role=goal["target_role"], grade=goal["target_grade"]).exists():
            raise ValidationError({"career_goal": "Unknown role and grade combination."})
        employee.career_goal = dict(goal)
        employee.save(update_fields=["career_goal"])
        return Response(career_payload(employee))


class QuestStartView(APIView):
    @transaction.atomic
    def post(self, request, event_id: str):
        serializer = QuestActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = scoped_employee(request, serializer.validated_data["employee_id"])
        event = get_object_or_404(LearningEvent, pk=event_id)
        validate_quest_eligibility(employee, event)
        if employee.activities.filter(event=event, status="completed").exists() and event_id != "EV_036":
            raise ValidationError({"event_id": "This event has already been completed."})
        quest, created = EmployeeQuest.objects.get_or_create(employee=employee, event=event)
        if quest and quest.state == EmployeeQuest.State.COMPLETED:
            if event_id == "EV_036":
                quest.state = EmployeeQuest.State.ACTIVE
                quest.started_at = timezone.now()
                quest.completed_at = None
                quest.xp_awarded = 0
                quest.save(update_fields=["state", "started_at", "completed_at", "xp_awarded"])
                return Response(
                    {
                        "state": quest.state,
                        "event_id": event_id,
                        "started_at": quest.started_at.isoformat(),
                        "idempotent": False,
                        "restarted": True,
                    },
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {
                    "state": quest.state,
                    "event_id": event_id,
                    "xp_awarded": quest.xp_awarded,
                    "idempotent": True,
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {
                "state": quest.state,
                "event_id": event_id,
                "started_at": quest.started_at.isoformat(),
                "idempotent": not created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class QuestCompleteView(APIView):
    @transaction.atomic
    def post(self, request, event_id: str):
        serializer = QuestActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = scoped_employee(request, serializer.validated_data["employee_id"])
        event = get_object_or_404(LearningEvent, pk=event_id)
        if event.mandatory:
            raise ValidationError({"event_id": "Mandatory events are not Career Quest recommendations."})
        quest = EmployeeQuest.objects.select_for_update().filter(employee=employee, event=event).first()
        if quest and quest.state == EmployeeQuest.State.COMPLETED:
            return Response(
                {
                    "state": quest.state,
                    "event_id": event_id,
                    "xp_awarded": quest.xp_awarded,
                    "idempotent": True,
                    "dashboard": dashboard(employee),
                }
            )

        validate_quest_eligibility(employee, event)
        if quest is None:
            if not employee.activities.filter(event=event, status="in_progress").exists():
                raise ValidationError({"event_id": "Start the quest before completing it."})
            quest = EmployeeQuest.objects.create(employee=employee, event=event)

        critical_open = {
            item["skill_id"]
            for item in skill_gap(employee)
            if item["critical"] and item["gap"] > 0
        }
        develops = {item["skill_id"] for item in event.develops_skills}
        bonus_eligible = bool(critical_open & develops)
        completed_at = timezone.now()
        if event_id == "EV_036":
            record_id = f"DEMO-{employee.external_id}-{event.external_id}-{completed_at:%Y%m%d%H%M%S%f}"
        else:
            record_id = f"DEMO-{employee.external_id}-{event.external_id}"

        ActivityHistory.objects.get_or_create(
            record_id=record_id,
            defaults={
                "employee": employee,
                "event": event,
                "date": settings.CAREER_SNAPSHOT_DATE,
                "status": "completed",
                "completion_pct": 100,
                "assigned_by": "self",
            },
        )
        bonus_awarded = 0
        if bonus_eligible:
            _, bonus_created = XPTransaction.objects.get_or_create(
                employee=employee,
                event=event,
                reason="critical_gap_bonus",
                defaults={"amount": 100},
            )
            bonus_awarded = 100 if bonus_created else 0
        xp_awarded = 200 + bonus_awarded

        quest.state = EmployeeQuest.State.COMPLETED
        quest.completed_at = completed_at
        quest.xp_awarded = xp_awarded
        quest.save(update_fields=["state", "completed_at", "xp_awarded"])

        return Response(
            {
                "state": quest.state,
                "event_id": event_id,
                "xp_awarded": xp_awarded,
                "idempotent": False,
                "dashboard": dashboard(employee),
            }
        )


class CoachView(APIView):
    def post(self, request):
        serializer = CoachRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = scoped_employee(request, serializer.validated_data["employee_id"])
        return Response(
            coach_answer(
                employee,
                serializer.validated_data["question"],
                serializer.validated_data["language"],
            )
        )


class HROverviewView(APIView):
    def get(self, request):
        if demo_role(request) != "hr":
            raise PermissionDenied("Switch to the HR demo role to open this view.")
        return Response(hr_overview())
