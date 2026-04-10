from rest_framework import serializers
from .models import AttendanceRecord, AttendanceModRequest, Project
from datetime import date


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Project
        fields = ['id', 'code', 'name', 'is_active']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    project_name  = serializers.CharField(source='project.name', read_only=True)
    work_minutes  = serializers.IntegerField(read_only=True)
    overtime_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model  = AttendanceRecord
        fields = [
            'id', 'date', 'clock_in', 'clock_out', 'break_minutes',
            'status', 'note', 'project', 'project_name',
            'work_minutes', 'overtime_minutes',
        ]
        read_only_fields = ['id', 'status']


class ClockInSerializer(serializers.Serializer):
    project_id = serializers.UUIDField(required=False, allow_null=True)
    note       = serializers.CharField(required=False, allow_blank=True)


class ClockOutSerializer(serializers.Serializer):
    break_minutes = serializers.IntegerField(default=60, min_value=0)


class AttendanceModRequestSerializer(serializers.ModelSerializer):
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)
    date           = serializers.DateField(source='attendance.date', read_only=True)

    class Meta:
        model  = AttendanceModRequest
        fields = [
            'id', 'attendance', 'date', 'applicant_name',
            'requested_clock_in', 'requested_clock_out',
            'reason', 'status', 'approved_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'created_at']


class AttendanceSummarySerializer(serializers.Serializer):
    year_month           = serializers.CharField()
    total_work_days      = serializers.IntegerField()
    total_work_minutes   = serializers.IntegerField()
    total_overtime_minutes = serializers.IntegerField()
    overtime_alert       = serializers.BooleanField()
