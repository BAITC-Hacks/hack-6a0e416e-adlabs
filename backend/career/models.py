from __future__ import annotations

from django.db import models


class Skill(models.Model):
    external_id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=160)
    type = models.CharField(max_length=32)
    category = models.CharField(max_length=96)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class RoleProfile(models.Model):
    role = models.CharField(max_length=120)
    grade = models.CharField(max_length=32)
    required_skills = models.JSONField(default=dict)
    critical_skills = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["role", "grade"], name="unique_role_grade")
        ]
        ordering = ["role", "grade"]

    def __str__(self) -> str:
        return f"{self.role} / {self.grade}"


class Employee(models.Model):
    external_id = models.CharField(max_length=32, primary_key=True)
    full_name = models.CharField(max_length=160)
    department = models.CharField(max_length=160)
    role = models.CharField(max_length=120)
    grade = models.CharField(max_length=32)
    manager = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    hire_date = models.DateField()
    tenure_months = models.PositiveIntegerField(default=0)
    work_format = models.CharField(max_length=32)
    preferred_language = models.CharField(max_length=8, default="ru")
    career_goal = models.JSONField(null=True, blank=True)
    skills = models.JSONField(default=dict)
    last_review_date = models.DateField()

    class Meta:
        ordering = ["full_name", "external_id"]

    def __str__(self) -> str:
        return f"{self.full_name} ({self.external_id})"


class LearningEvent(models.Model):
    external_id = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=48)
    format = models.CharField(max_length=32)
    duration_hours = models.DecimalField(max_digits=7, decimal_places=1)
    mandatory = models.BooleanField(default=False)
    target_roles = models.JSONField(default=list)
    target_grades = models.JSONField(default=list)
    develops_skills = models.JSONField(default=list)
    prerequisites = models.JSONField(default=dict)
    upcoming_sessions = models.JSONField(default=list)

    class Meta:
        ordering = ["external_id"]

    def __str__(self) -> str:
        return self.title


class ActivityHistory(models.Model):
    record_id = models.CharField(max_length=64, primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="activities")
    event = models.ForeignKey(LearningEvent, on_delete=models.CASCADE, related_name="activities")
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32)
    completion_pct = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    feedback_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    assigned_by = models.CharField(max_length=32)

    class Meta:
        ordering = ["date", "record_id"]
        indexes = [
            models.Index(fields=["employee", "status"]),
            models.Index(fields=["event", "status"]),
        ]


class EmployeeQuest(models.Model):
    class State(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="quests")
    event = models.ForeignKey(LearningEvent, on_delete=models.CASCADE, related_name="employee_quests")
    state = models.CharField(max_length=16, choices=State.choices, default=State.ACTIVE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    xp_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["employee", "event"], name="unique_employee_quest")
        ]
        ordering = ["-started_at"]


class XPTransaction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="xp_transactions")
    event = models.ForeignKey(
        LearningEvent,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="xp_transactions",
    )
    amount = models.IntegerField()
    reason = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "event", "reason"], name="unique_employee_event_xp_reason"
            )
        ]
        ordering = ["created_at"]
