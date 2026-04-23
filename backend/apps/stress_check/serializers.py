from rest_framework import serializers
from .models import StressCheckPeriod, StressCheckResponse, STRESS_CHECK_QUESTIONS


class StressCheckPeriodSerializer(serializers.ModelSerializer):
    response_count = serializers.SerializerMethodField()
    high_stress_count = serializers.SerializerMethodField()

    class Meta:
        model = StressCheckPeriod
        fields = [
            'id', 'title', 'start_date', 'end_date', 'is_published',
            'response_count', 'high_stress_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_response_count(self, obj):
        return obj.responses.filter(is_submitted=True).count()

    def get_high_stress_count(self, obj):
        return obj.responses.filter(high_stress=True).count()


class StressCheckResponseSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = StressCheckResponse
        fields = [
            'id', 'period', 'employee', 'employee_name', 'answers',
            'submitted_at', 'is_submitted', 'high_stress', 'total_score', 'questions',
        ]
        read_only_fields = ['id', 'submitted_at', 'is_submitted', 'high_stress', 'total_score']

    def get_questions(self, obj):
        return STRESS_CHECK_QUESTIONS
