from django.contrib import admin

from .models import ActivityHistory, Employee, EmployeeQuest, LearningEvent, RoleProfile, Skill, XPTransaction


admin.site.register([Skill, RoleProfile, Employee, LearningEvent, ActivityHistory, EmployeeQuest, XPTransaction])
