from django.db import models

class Employee(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=120)
    grade = models.CharField(max_length=40)
    department = models.CharField(max_length=120, blank=True)
    last_review_date = models.DateField()
    baseline_skills = models.JSONField(default=dict)
    career_goal = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.external_id})"

class Skill(models.Model):
    external_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class RoleProfile(models.Model):
    role = models.CharField(max_length=120)
    grade = models.CharField(max_length=40)
    required_skills = models.JSONField(default=dict)
    critical_skills = models.JSONField(default=list)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["role", "grade"], name="unique_role_grade")]

class LearningEvent(models.Model):
    external_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    duration_hours = models.FloatField(default=0)
    format = models.CharField(max_length=40, blank=True)
    mandatory = models.BooleanField(default=False)
    repeatable = models.BooleanField(default=False)
    target_roles = models.JSONField(default=list)
    target_grades = models.JSONField(default=list)
    develops_skills = models.JSONField(default=list)
    prerequisites = models.JSONField(default=dict)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.title

class ActivityHistory(models.Model):
    external_id = models.CharField(max_length=60, unique=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="activities")
    event = models.ForeignKey(LearningEvent, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=30)
    completion_pct = models.PositiveSmallIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["date", "external_id"]

class EmployeeQuest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="quests")
    event = models.ForeignKey(LearningEvent, on_delete=models.CASCADE)
    state = models.CharField(max_length=20, default="active")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    xp_awarded = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["employee", "event"], name="unique_employee_event_quest")]

class XPTransaction(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="xp_transactions")
    quest = models.OneToOneField(EmployeeQuest, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    reason = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
