from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("employees/", views.employees),
    path("employees/<str:employee_id>/", views.employee_profile),
    path("employees/<str:employee_id>/dashboard/", views.dashboard),
    path("employees/<str:employee_id>/skills/", views.skills),
    path("employees/<str:employee_id>/career/", views.career),
    path("career-options/", views.career_options),
    path("employees/<str:employee_id>/recommendations/", views.recommendations),
    path("employees/<str:employee_id>/quests/", views.quests),
    path("employees/<str:employee_id>/career-goal/", views.change_goal),
    path("employees/<str:employee_id>/chat-history/", views.chat_history),
    path("quests/<str:event_id>/start/", views.start_quest),
    path("quests/<str:event_id>/complete/", views.complete_quest),
    path("ai/chat/", views.chat),
]
