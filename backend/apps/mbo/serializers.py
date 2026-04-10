from rest_framework import serializers
from .models import MBOGoal, MBOReport, DailyReport


class MBOReportSerializer(serializers.ModelSerializer):
    class Meta:
        model  = MBOReport
        fields = [
            'id', 'goal', 'month', 'action_content', 'result',
            'manager_comment', 'ai_suggestion', 'status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'manager_comment', 'ai_suggestion', 'created_at', 'updated_at']


class MBOGoalSerializer(serializers.ModelSerializer):
    reports      = MBOReportSerializer(many=True, read_only=True)
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = MBOGoal
        fields = [
            'id', 'year', 'period', 'title', 'target_level', 'weight',
            'self_score', 'manager_score', 'status',
            'employee_name', 'reports',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'manager_score', 'employee_name', 'created_at', 'updated_at']

    def validate_weight(self, value):
        if not (0 < value <= 100):
            raise serializers.ValidationError('ウェイトは1〜100の間で設定してください')
        return value


class DailyReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = DailyReport
        fields = [
            'id', 'report_date', 'content', 'ai_suggestion', 'status',
            'employee_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'ai_suggestion', 'employee_name', 'created_at', 'updated_at']
