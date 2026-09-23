from django.contrib import admin
from .models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, Skill, XPTransaction

for model in (Employee, Skill, RoleProfile, LearningEvent, ActivityHistory, EmployeeQuest, XPTransaction):
    admin.site.register(model)
