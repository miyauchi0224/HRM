from django.contrib import admin
from .models import Project, AttendanceRecord, AttendanceModRequest


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'manager', 'is_active', 'start_date', 'end_date']
    list_filter   = ['is_active']
    search_fields = ['code', 'name']


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'date', 'clock_in', 'clock_out', 'status', 'project']
    list_filter   = ['status', 'date']
    search_fields = ['employee__last_name', 'employee__first_name']
    date_hierarchy = 'date'


@admin.register(AttendanceModRequest)
class AttendanceModRequestAdmin(admin.ModelAdmin):
    list_display  = ['applicant', 'attendance', 'status', 'created_at']
    list_filter   = ['status']
