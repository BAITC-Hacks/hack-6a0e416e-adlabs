from django.urls import path

from .api import (
    CareerGoalView,
    CareerView,
    CoachView,
    DashboardView,
    EmployeeDetailView,
    EmployeeListView,
    HROverviewView,
    HealthView,
    QuestCompleteView,
    QuestListView,
    QuestStartView,
    RecommendationView,
    RoleProfileListView,
    SkillsView,
)


urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("employees/", EmployeeListView.as_view(), name="employee-list"),
    path("employees/<str:employee_id>/", EmployeeDetailView.as_view(), name="employee-detail"),
    path("employees/<str:employee_id>/dashboard/", DashboardView.as_view(), name="dashboard"),
    path("employees/<str:employee_id>/skills/", SkillsView.as_view(), name="skills"),
    path("employees/<str:employee_id>/career/", CareerView.as_view(), name="career"),
    path(
        "employees/<str:employee_id>/recommendations/",
        RecommendationView.as_view(),
        name="recommendations",
    ),
    path("employees/<str:employee_id>/quests/", QuestListView.as_view(), name="quests"),
    path("employees/<str:employee_id>/career-goal/", CareerGoalView.as_view(), name="career-goal"),
    path("role-profiles/", RoleProfileListView.as_view(), name="role-profile-list"),
    path("quests/<str:event_id>/start/", QuestStartView.as_view(), name="quest-start"),
    path("quests/<str:event_id>/complete/", QuestCompleteView.as_view(), name="quest-complete"),
    path("ai/chat/", CoachView.as_view(), name="coach"),
    path("hr/overview/", HROverviewView.as_view(), name="hr-overview"),
]
