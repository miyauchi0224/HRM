from rest_framework import serializers
from .models import HealthCheckup


class HealthCheckupSerializer(serializers.ModelSerializer):
    employee_name      = serializers.CharField(source='employee.full_name', read_only=True)
    department         = serializers.CharField(source='employee.department', read_only=True)
    checkup_type_label = serializers.CharField(source='get_checkup_type_display', read_only=True)
    result_label       = serializers.CharField(source='get_result_display', read_only=True)
    followup_required  = serializers.BooleanField(read_only=True)
    followup_pending   = serializers.BooleanField(read_only=True)

    class Meta:
        model  = HealthCheckup
        fields = [
            'id', 'employee', 'employee_name', 'department', 'fiscal_year',
            'checkup_type', 'checkup_type_label', 'scheduled_date', 'checkup_date', 'institution',
            'result', 'result_label', 'followup_required', 'followup_pending',
            'followup_due_date', 'followup_completed_date', 'note', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        result   = data.get('result', getattr(self.instance, 'result', ''))
        checkup  = data.get('checkup_date', getattr(self.instance, 'checkup_date', None))
        due      = data.get('followup_due_date', getattr(self.instance, 'followup_due_date', None))
        if result and not checkup:
            raise serializers.ValidationError({'checkup_date': '判定を入力するときは受診日も入力してください'})
        if due and checkup and due < checkup:
            raise serializers.ValidationError({'followup_due_date': '期限は受診日以降にしてください'})
        return data
