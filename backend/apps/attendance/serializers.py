from rest_framework import serializers
from .models import AttendanceRecord, AttendanceProjectRecord, AttendanceModRequest, Project
from datetime import date


class ProjectSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model  = Project
        fields = ['id', 'code', 'name', 'manager', 'manager_name', 'is_active']

    def validate_manager(self, value):
        if value is None:
            raise serializers.ValidationError('管理者は必須です。')
        return value


class AttendanceProjectRecordSerializer(serializers.ModelSerializer):
    project_code = serializers.CharField(source='project.code', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model  = AttendanceProjectRecord
        fields = ['id', 'project', 'project_code', 'project_name', 'minutes']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    project_records  = AttendanceProjectRecordSerializer(many=True, required=False)
    work_minutes     = serializers.IntegerField(read_only=True)
    overtime_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model  = AttendanceRecord
        fields = [
            'id', 'date', 'clock_in', 'clock_out',
            'stamped_clock_in', 'stamped_clock_out',
            'break_minutes', 'status', 'note', 'project_records',
            'work_minutes', 'overtime_minutes',
        ]
        read_only_fields = ['id', 'status', 'stamped_clock_in', 'stamped_clock_out']

    def validate(self, data):
        project_records = data.get('project_records')
        if project_records:
            # プロジェクト合計分数 ≦ 労働時間（clock_in/out は更新中の値 or 既存値を使う）
            clock_in  = data.get('clock_in')  or getattr(self.instance, 'clock_in',  None)
            clock_out = data.get('clock_out') or getattr(self.instance, 'clock_out', None)
            break_min = data.get('break_minutes', None)
            if break_min is None:
                break_min = getattr(self.instance, 'break_minutes', 60)

            if clock_in and clock_out:
                from datetime import datetime, date as d
                ci = datetime.combine(d.today(), clock_in)
                co = datetime.combine(d.today(), clock_out)
                work = max(0, int((co - ci).total_seconds() / 60) - break_min)
                total_pj = sum(pr['minutes'] for pr in project_records)
                if total_pj > work:
                    raise serializers.ValidationError(
                        f'プロジェクト合計（{total_pj}分）が労働時間（{work}分）を超えています。'
                    )
        return data

    def update(self, instance, validated_data):
        project_records_data = validated_data.pop('project_records', None)
        instance = super().update(instance, validated_data)
        if project_records_data is not None:
            instance.project_records.all().delete()
            for pr in project_records_data:
                AttendanceProjectRecord.objects.create(attendance=instance, **pr)
        return instance


class ClockInSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True)


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
    year_month             = serializers.CharField()
    total_work_days        = serializers.IntegerField()
    total_work_minutes     = serializers.IntegerField()
    total_overtime_minutes = serializers.IntegerField()
    overtime_alert         = serializers.BooleanField()
