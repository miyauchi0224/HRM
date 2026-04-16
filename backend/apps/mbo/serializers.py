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
    reports           = MBOReportSerializer(many=True, read_only=True)
    employee_name     = serializers.CharField(source='employee.full_name', read_only=True)
    period_months_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = MBOGoal
        fields = [
            'id', 'year', 'period', 'period_start_month', 'period_end_month',
            'period_months_count', 'title', 'target_level', 'weight',
            'self_score', 'manager_score', 'status',
            'employee_name', 'reports',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'manager_score', 'employee_name', 'period_months_count',
                            'created_at', 'updated_at']

    def validate_weight(self, value):
        if not (0 < value <= 100):
            raise serializers.ValidationError('ウェイトは1〜100の間で設定してください')
        return value

    def validate(self, data):
        start = data.get('period_start_month')
        end   = data.get('period_end_month')
        if start is not None or end is not None:
            if not (start and end):
                raise serializers.ValidationError('期間開始月と終了月は両方指定してください')
            if not (1 <= start <= 12 and 1 <= end <= 12):
                raise serializers.ValidationError('月は1〜12の範囲で指定してください')
            if start > end:
                raise serializers.ValidationError('開始月は終了月以前に設定してください')
            if (end - start + 1) > 6:
                raise serializers.ValidationError('期間は最大6ヶ月（半期）です')
        return data


class DailyReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = DailyReport
        fields = [
            'id', 'report_date', 'content', 'ai_suggestion', 'status',
            'employee_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'ai_suggestion', 'employee_name', 'created_at', 'updated_at']
