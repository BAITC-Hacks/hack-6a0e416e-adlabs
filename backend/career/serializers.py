from rest_framework import serializers


class CareerGoalSerializer(serializers.Serializer):
    target_role = serializers.CharField(max_length=120)
    target_grade = serializers.ChoiceField(choices=["Junior", "Middle", "Senior", "Lead"])


class QuestActionSerializer(serializers.Serializer):
    employee_id = serializers.CharField(max_length=32)


class CoachRequestSerializer(serializers.Serializer):
    employee_id = serializers.CharField(max_length=32)
    question = serializers.CharField(max_length=1200)
    language = serializers.ChoiceField(choices=["ru", "en", "kk"], default="ru")
