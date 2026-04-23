from rest_framework import serializers
from .models import (
    OnboardingTemplate,
    OnboardingTemplateTask,
    OnboardingAssignment,
    OnboardingTaskItem,
)


class OnboardingTemplateTaskSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = OnboardingTemplateTask
        fields = [
            'id', 'title', 'description', 'category', 'category_label',
            'due_days_from_hire', 'order',
        ]
        read_only_fields = ['id']


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    tasks = OnboardingTemplateTaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = OnboardingTemplate
        fields = [
            'id', 'name', 'description', 'is_active',
            'task_count', 'tasks', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_task_count(self, obj):
        return obj.tasks.count()


class OnboardingTaskItemSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='template_task.title', read_only=True)
    task_description = serializers.CharField(source='template_task.description', read_only=True)
    task_category = serializers.CharField(source='template_task.category', read_only=True)
    task_category_label = serializers.CharField(
        source='template_task.get_category_display', read_only=True
    )
    due_days_from_hire = serializers.IntegerField(
        source='template_task.due_days_from_hire', read_only=True
    )

    class Meta:
        model = OnboardingTaskItem
        fields = [
            'id', 'task_title', 'task_description', 'task_category',
            'task_category_label', 'due_days_from_hire',
            'is_completed', 'completed_at',
        ]
        read_only_fields = ['id', 'completed_at']


class OnboardingAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    template_name = serializers.CharField(source='template.name', read_only=True)
    assigned_by_name = serializers.CharField(
        source='assigned_by.full_name', read_only=True, default=None
    )
    progress_percent = serializers.IntegerField(read_only=True)
    task_items = OnboardingTaskItemSerializer(many=True, read_only=True)

    class Meta:
        model = OnboardingAssignment
        fields = [
            'id', 'template', 'template_name', 'employee', 'employee_name',
            'assigned_by_name', 'assigned_at', 'progress_percent', 'task_items',
        ]
        read_only_fields = [
            'id', 'assigned_at', 'assigned_by_name', 'progress_percent',
        ]
