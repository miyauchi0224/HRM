from rest_framework import serializers
from .models import SalaryGrade, Allowance, EmployeeAllowance, Payslip


class SalaryGradeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SalaryGrade
        fields = ['id', 'grade', 'base_salary', 'valid_from', 'valid_to']


class AllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Allowance
        fields = ['id', 'name', 'allowance_type', 'amount', 'is_active']


class EmployeeAllowanceSerializer(serializers.ModelSerializer):
    allowance_name = serializers.CharField(source='allowance.name', read_only=True)
    allowance_type = serializers.CharField(source='allowance.allowance_type', read_only=True)
    effective_amount = serializers.SerializerMethodField()

    class Meta:
        model  = EmployeeAllowance
        fields = ['id', 'allowance', 'allowance_name', 'allowance_type',
                  'amount', 'effective_amount', 'valid_from', 'valid_to']

    def get_effective_amount(self, obj):
        """個別金額があればそちら、なければマスタ金額"""
        return obj.amount if obj.amount is not None else obj.allowance.amount


class PayslipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = Payslip
        fields = [
            'id', 'year', 'month', 'employee_name',
            'base_salary', 'total_allowances', 'overtime_pay', 'gross_salary',
            'health_insurance', 'pension', 'employment_insurance',
            'income_tax', 'resident_tax', 'total_deductions', 'net_salary',
            'status', 'payslip_url', 'created_at',
        ]
        read_only_fields = ['id', 'employee_name', 'created_at']
