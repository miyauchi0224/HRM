from rest_framework import serializers
from .models import LeaveBalance, LeaveRequest


class LeaveBalanceSerializer(serializers.ModelSerializer):
    remaining_days = serializers.DecimalField(max_digits=4, decimal_places=1, read_only=True)

    class Meta:
        model  = LeaveBalance
        fields = ['id', 'fiscal_year', 'granted_days', 'used_days',
                  'carried_days', 'remaining_days']
        read_only_fields = ['id']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    approver_name = serializers.CharField(source='approver.full_name', read_only=True, default=None)

    class Meta:
        model  = LeaveRequest
        fields = [
            'id', 'leave_type', 'start_date', 'end_date', 'days',
            'reason', 'status', 'approved_at', 'created_at',
            'employee_name', 'approver_name',
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'created_at',
                            'employee_name', 'approver_name']

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError('開始日は終了日以前である必要があります')
        return data
