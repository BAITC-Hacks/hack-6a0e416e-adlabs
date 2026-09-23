import os
from datetime import date, timedelta

from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, XPTransaction
from .services import career_snapshot


def error(code, message, status=400, details=None):
    return Response({"error": {"code": code, "message": message, "details": details or {}}}, status=status)


def selected_employee(request):
    # Demo selector is explicit and must be replaced by authenticated identity before production.
    employee_id = request.data.get("employee_id") if request.method == "POST" else None
    return get_object_or_404(Employee, external_id=employee_id)


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def employees(request):
    term = request.query_params.get("q", "").strip()[:100]
    records = Employee.objects.all().order_by("external_id")
    if term:
        from django.db.models import Q
        records = records.filter(Q(full_name__icontains=term) | Q(external_id__icontains=term)
                                 | Q(role__icontains=term))
    return Response([{"id": e.external_id, "name": e.full_name, "role": e.role,
                      "grade": e.grade, "language": e.metadata.get("preferred_language", "ru")}
                     for e in records[:200]])


@api_view(["GET"])
def employee_profile(request, employee_id):
    e = get_object_or_404(Employee, external_id=employee_id)
    snap = career_snapshot(e)
    return Response({key: snap[key] for key in ("employee", "goal", "xp", "rank")})


@api_view(["GET"])
def dashboard(request, employee_id):
    e = get_object_or_404(Employee, external_id=employee_id)
    snap = career_snapshot(e)
    return Response({**snap, "top_gaps": [g for g in snap["gaps"] if g["gap"] > 0][:5],
                     "next_quest": next((q for q in snap["recommendations"] if not q["locked"]), None)})


@api_view(["GET"])
def skills(request, employee_id):
    s = career_snapshot(get_object_or_404(Employee, external_id=employee_id))
    return Response({key: s[key] for key in ("effective_skills", "gaps", "readiness", "goal")})


@api_view(["GET"])
def career(request, employee_id):
    s = career_snapshot(get_object_or_404(Employee, external_id=employee_id))
    return Response({key: s[key] for key in ("employee", "goal", "gaps", "readiness", "recommendations")})


@api_view(["GET"])
def career_options(request):
    return Response([{"role": role, "grade": grade}
                     for role, grade in RoleProfile.objects.order_by("role", "grade").values_list("role", "grade")])


@api_view(["GET"])
def recommendations(request, employee_id):
    return Response(career_snapshot(get_object_or_404(Employee, external_id=employee_id))["recommendations"])


@api_view(["GET"])
def quests(request, employee_id):
    s = career_snapshot(get_object_or_404(Employee, external_id=employee_id))
    return Response({key: s[key] for key in ("recommendations", "active_quests", "completed_quests")})


@api_view(["POST"])
def change_goal(request, employee_id):
    if not settings.DEMO_MODE:
        return error("DEMO_DISABLED", "Goal editing requires demo mode", 403)
    role = request.data.get("target_role")
    grade = request.data.get("target_grade")
    if not RoleProfile.objects.filter(role=role, grade=grade).exists():
        return error("INVALID_CAREER_GOAL", "Unknown role or grade")
    e = get_object_or_404(Employee, external_id=employee_id)
    e.career_goal = {"target_role": role, "target_grade": grade}
    e.save(update_fields=["career_goal"])
    return Response({"goal": e.career_goal})


@api_view(["POST"])
def start_quest(request, event_id):
    if not settings.DEMO_MODE:
        return error("DEMO_DISABLED", "Quest actions require demo mode", 403)
    employee = selected_employee(request)
    event = get_object_or_404(LearningEvent, external_id=event_id)
    snap = career_snapshot(employee)
    match = next((q for q in snap["recommendations"] if q["event_id"] == event_id), None)
    if not match:
        return error("QUEST_UNAVAILABLE", "Event is not recommended for this employee")
    if match["locked"]:
        return error("PREREQUISITE_UNMET", "Complete prerequisites first", details={
            "unmet_prerequisites": match["unmet_prerequisites"]})
    with transaction.atomic():
        quest, created = EmployeeQuest.objects.get_or_create(employee=employee, event=event,
                                                              defaults={"state": "active"})
        if not created and quest.state == "completed":
            return error("QUEST_COMPLETED", "Quest has already been completed")
    return Response({"event_id": event_id, "state": "active"})


@api_view(["POST"])
def complete_quest(request, event_id):
    if not settings.DEMO_MODE:
        return error("DEMO_DISABLED", "Quest actions require demo mode", 403)
    employee = selected_employee(request)
    event = get_object_or_404(LearningEvent, external_id=event_id)
    with transaction.atomic():
        quest = EmployeeQuest.objects.select_for_update().filter(employee=employee, event=event).first()
        if not quest and ActivityHistory.objects.filter(employee=employee, event=event, status="in_progress").exists():
            quest = EmployeeQuest.objects.create(employee=employee, event=event, state="active")
        if not quest:
            return error("QUEST_NOT_STARTED", "Start the quest first")
        if quest.state == "completed":
            return error("QUEST_COMPLETED", "Quest has already been completed")
        before = career_snapshot(employee)
        critical_ids = {g["skill_id"] for g in before["gaps"] if g["critical"] and g["gap"] > 0}
        bonus = settings.QUEST_XP_CRITICAL_BONUS if any(
            g["skill_id"] in critical_ids for g in event.develops_skills) else 0
        xp = settings.QUEST_XP_BASE + bonus
        quest.state = "completed"
        quest.completed_at = timezone.now()
        quest.xp_awarded = xp
        quest.save(update_fields=["state", "completed_at", "xp_awarded"])
        ActivityHistory.objects.create(external_id=f"DEMO-{quest.pk}", employee=employee,
                                       event=event, date=max(date.today(), employee.last_review_date + timedelta(days=1)),
                                       status="completed",
                                       completion_pct=100, metadata={"demo": True})
        XPTransaction.objects.create(employee=employee, quest=quest, amount=xp, reason="quest_completed")
        after = career_snapshot(employee)
    changed = [{"skill_id": sid, "before": value, "after": after["effective_skills"].get(sid, 0)}
               for sid, value in before["effective_skills"].items()
               if after["effective_skills"].get(sid, 0) > value]
    return Response({"event_id": event_id, "xp_awarded": xp, "skills_changed": changed,
                     "readiness_before": before["readiness"], "readiness_after": after["readiness"],
                     "next_quest": next((q for q in after["recommendations"] if not q["locked"]), None)})


@api_view(["POST"])
def chat(request):
    employee = selected_employee(request)
    question = str(request.data.get("message", "")).strip()[:1000]
    language = request.data.get("language", "ru")
    if language not in ("ru", "en", "kk"):
        language = "ru"
    if not question:
        return error("MESSAGE_REQUIRED", "Enter a question")
    snap = career_snapshot(employee)
    allowed = {"employee": snap["employee"], "goal": snap["goal"], "readiness": snap["readiness"],
               "gaps": snap["gaps"], "recommendations": [
                   {"event_id": q["event_id"], "title": q["title"], "reasons": q["reasons"],
                    "locked": q["locked"], "chain": q["chain"], "readiness_after": q["readiness_after"]}
                   for q in snap["recommendations"][:5]]}
    key = os.getenv("OPENAI_API_KEY")
    if key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=key, timeout=20)
            response = client.responses.create(
                model=settings.OPENAI_MODEL,
                instructions=(f"You are Career Quest's career coach. Answer in language code {language}. "
                              "Use only the supplied structured employee context. Never invent events, "
                              "skill values or readiness. Do not claim to change quest state. "
                              "If data is missing, say so. Keep answers concise."),
                input=f"Context: {allowed}\nEmployee question: {question}",
                store=False,
            )
            return Response({"answer": response.output_text, "mode": "openai"})
        except Exception:
            return error("AI_PROVIDER_UNAVAILABLE", "AI provider is temporarily unavailable", 503)
    gaps = sorted((g for g in snap["gaps"] if g["gap"] > 0),
                  key=lambda g: (-g["critical"], -g["gap"], g["name"]))
    next_quest = next((q for q in snap["recommendations"] if not q["locked"]), None)
    copy = {
        "ru": ("Карьерная цель не задана. Выберите роль и грейд.",
               "Готовность: {readiness}%. Главные пробелы: {skills}. Следующий шаг: {title} ({event_id}). Прогноз: {after}%.",
               "Готовность: {readiness}%. Подходящих доступных квестов сейчас нет."),
        "en": ("Career goal is not set. Choose a target role and grade.",
               "Readiness: {readiness}%. Main gaps: {skills}. Next step: {title} ({event_id}). Projected readiness: {after}%.",
               "Readiness: {readiness}%. No available quest matches the current gaps."),
        "kk": ("Мансап мақсаты белгіленбеген. Рөл мен грейдті таңдаңыз.",
               "Дайындық: {readiness}%. Негізгі олқылықтар: {skills}. Келесі қадам: {title} ({event_id}). Болжам: {after}%.",
               "Дайындық: {readiness}%. Қазір сәйкес қолжетімді тапсырма жоқ."),
    }[language]
    if not snap["goal"]:
        answer = copy[0]
    elif next_quest:
        answer = copy[1].format(readiness=snap["readiness"], skills=", ".join(g["name"] for g in gaps[:3]),
                                title=next_quest["title"], event_id=next_quest["event_id"],
                                after=next_quest["readiness_after"])
    else:
        answer = copy[2].format(readiness=snap["readiness"])
    return Response({"answer": answer, "mode": "deterministic"})
