from rest_framework import serializers
from .models import TodoItem, DailyReport


class TodoItemSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    project_code = serializers.CharField(source='project.code', read_only=True, default=None)

    class Meta:
        model  = TodoItem
        fields = [
            'id', 'title', 'description', 'status', 'due_date', 'order',
            'project', 'project_name', 'project_code',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'project_name', 'project_code', 'created_at', 'updated_at']


class DailyReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = DailyReport
        fields = [
            'id', 'report_date', 'content', 'tomorrow', 'issues', 'status',
            'employee_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'employee_name', 'created_at', 'updated_at']
