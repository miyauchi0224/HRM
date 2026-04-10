from django.contrib import admin
from .models import SalaryGrade, Allowance, EmployeeAllowance, Payslip


@admin.register(SalaryGrade)
class SalaryGradeAdmin(admin.ModelAdmin):
    list_display = ['grade', 'base_salary', 'valid_from', 'valid_to']


@admin.register(Allowance)
class AllowanceAdmin(admin.ModelAdmin):
    list_display = ['name', 'allowance_type', 'amount', 'is_active']
    list_filter  = ['is_active', 'allowance_type']


@admin.register(EmployeeAllowance)
class EmployeeAllowanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'allowance', 'amount', 'valid_from', 'valid_to']


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'year', 'month', 'gross_salary', 'net_salary', 'status']
    list_filter   = ['status', 'year', 'month']
    search_fields = ['employee__last_name', 'employee__first_name']
