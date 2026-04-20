from rest_framework import serializers
from .models import ApprovalRequest, ApprovalStep, ApprovalTemplate
from apps.employees.models import Employee


class ApprovalTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalTemplate
        fields = '__all__'


class ApprovalStepSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.full_name', read_only=True)
    step_role_label = serializers.CharField(source='get_step_role_display', read_only=True)

    class Meta:
        model = ApprovalStep
        fields = ['id', 'approver', 'approver_name', 'step_role', 'step_role_label',
                  'order', 'decision', 'comment', 'decided_at']


class ApprovalRequestSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)
    steps = ApprovalStepSerializer(many=True, read_only=True)
    approver_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = ApprovalRequest
        fields = [
            'id', 'title', 'category', 'applicant', 'applicant_name', 'template',
            'amount', 'content', 'attachments', 'status', 'submitted_at',
            'created_at', 'updated_at', 'steps', 'approver_ids',
        ]
        read_only_fields = ['applicant', 'status', 'submitted_at']

    def create(self, validated_data):
        approver_ids = validated_data.pop('approver_ids', [])
        request_obj = super().create(validated_data)
        for i, emp_id in enumerate(approver_ids):
            try:
                emp = Employee.objects.get(id=emp_id)
                ApprovalStep.objects.create(request=request_obj, approver=emp, order=i + 1)
            except Employee.DoesNotExist:
                pass
        return request_obj
