from django.contrib import admin
from .models import Employee, EmergencyContact, FamilyMember


class EmergencyContactInline(admin.TabularInline):
    model = EmergencyContact
    extra = 0


class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ['employee_number', 'full_name', 'department', 'position', 'grade', 'hire_date']
    list_filter   = ['department', 'employment_type', 'grade']
    search_fields = ['employee_number', 'last_name', 'first_name']
    inlines       = [EmergencyContactInline, FamilyMemberInline]
