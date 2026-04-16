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
    allowance_name   = serializers.CharField(source='allowance.name', read_only=True)
    allowance_type   = serializers.CharField(source='allowance.allowance_type', read_only=True)
    effective_amount = serializers.SerializerMethodField()

    class Meta:
        model  = EmployeeAllowance
        fields = ['id', 'allowance', 'allowance_name', 'allowance_type',
                  'amount', 'effective_amount', 'valid_from', 'valid_to']

    def get_effective_amount(self, obj):
        return obj.amount if obj.amount is not None else obj.allowance.amount


class PayslipSerializer(serializers.ModelSerializer):
    employee_name       = serializers.CharField(source='employee.full_name',       read_only=True)
    employee_number     = serializers.CharField(source='employee.employee_number', read_only=True)
    department          = serializers.CharField(source='employee.department',      read_only=True)
    # 銀行口座（表示のみ）
    bank_info           = serializers.SerializerMethodField()

    class Meta:
        model  = Payslip
        fields = [
            'id', 'year', 'month',
            'employee_name', 'employee_number', 'department', 'bank_info',
            # 支給
            'base_salary',
            'technical_allowance', 'secondment_allowance', 'housing_allowance',
            'overtime_pay', 'commute_allowance', 'family_allowance',
            'certification_allowance', 'position_allowance', 'special_allowance',
            'perfect_attendance_allowance', 'diligence_allowance', 'extra_overtime_pay',
            'total_allowances', 'gross_salary',
            # 控除
            'health_insurance', 'pension', 'employment_insurance', 'nursing_insurance',
            'social_insurance_total',
            'property_savings', 'company_housing_fee', 'union_fee', 'mutual_aid_fee',
            'employee_stock_contribution', 'other_deductions',
            'income_tax', 'resident_tax', 'total_deductions',
            # 差引
            'net_salary',
            # 勤怠
            'work_days', 'absence_days', 'paid_leave_days',
            # 管理
            'cutoff_date', 'payment_date', 'note', 'status', 'payslip_url', 'created_at',
        ]
        read_only_fields = [
            'id', 'employee_name', 'employee_number', 'department', 'bank_info',
            'total_allowances', 'gross_salary', 'social_insurance_total',
            'total_deductions', 'net_salary', 'created_at',
        ]

    def get_bank_info(self, obj):
        emp = obj.employee
        parts = []
        if emp.bank_name:
            parts.append(emp.bank_name)
        if emp.bank_branch:
            parts.append(emp.bank_branch)
        if emp.bank_account_type and emp.bank_account_number:
            parts.append(f'{emp.bank_account_type} {emp.bank_account_number}')
        if emp.bank_account_holder:
            parts.append(emp.bank_account_holder)
        return '　'.join(parts) if parts else ''
