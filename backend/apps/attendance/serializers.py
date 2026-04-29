from rest_framework import serializers
from .models import AttendanceRecord, AttendanceProjectRecord, AttendanceModRequest, Project, ProjectTask, ProjectManager
from datetime import date


class ManagerDetailSerializer(serializers.Serializer):
    """管理者詳細情報（ID + 名前）"""
    id = serializers.UUIDField()
    full_name = serializers.CharField()


class ProjectSerializer(serializers.ModelSerializer):
    # M2M対応：主管理者・従管理者リスト
    primary_managers = serializers.SerializerMethodField()
    secondary_managers = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    # 後方互換性：manager フィールド（廃止予定）
    manager = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()
    # IDリスト（書き込み用）
    primary_manager_ids = serializers.SerializerMethodField()
    secondary_manager_ids = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'description',
            'manager', 'manager_name', 'primary_managers', 'secondary_managers',
            'primary_manager_ids', 'secondary_manager_ids',
            'is_active', 'start_date', 'end_date', 'task_count'
        ]

    def get_primary_managers(self, obj):
        managers = obj.project_managers.filter(role=ProjectManager.Role.PRIMARY).select_related('employee')
        return [{'id': str(pm.employee.id), 'full_name': pm.employee.full_name} for pm in managers]

    def get_secondary_managers(self, obj):
        managers = obj.project_managers.filter(role=ProjectManager.Role.SECONDARY).select_related('employee')
        return [{'id': str(pm.employee.id), 'full_name': pm.employee.full_name} for pm in managers]

    def get_primary_manager_ids(self, obj):
        return [str(pm.employee.id) for pm in obj.project_managers.filter(role=ProjectManager.Role.PRIMARY)]

    def get_secondary_manager_ids(self, obj):
        return [str(pm.employee.id) for pm in obj.project_managers.filter(role=ProjectManager.Role.SECONDARY)]

    def get_manager(self, obj):
        """後方互換性：最初の主管理者を返す"""
        pm = obj.project_managers.filter(role=ProjectManager.Role.PRIMARY).first()
        return str(pm.employee.id) if pm else None

    def get_manager_name(self, obj):
        """後方互換性：最初の主管理者の名前を返す"""
        pm = obj.project_managers.filter(role=ProjectManager.Role.PRIMARY).select_related('employee').first()
        return pm.employee.full_name if pm else None

    def get_task_count(self, obj):
        return obj.tasks.count()

    def update(self, instance, validated_data):
        primary_ids = self.initial_data.get('primary_manager_ids', None)
        secondary_ids = self.initial_data.get('secondary_manager_ids', None)
        instance = super().update(instance, validated_data)

        if primary_ids is not None:
            from apps.employees.models import Employee
            # 既存のprimary を削除
            instance.project_managers.filter(role=ProjectManager.Role.PRIMARY).delete()
            # 新規追加
            for emp_id in primary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance,
                    employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.PRIMARY}
                )

        if secondary_ids is not None:
            from apps.employees.models import Employee
            # 既存のsecondary を削除
            instance.project_managers.filter(role=ProjectManager.Role.SECONDARY).delete()
            # 新規追加
            for emp_id in secondary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance,
                    employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.SECONDARY}
                )

        return instance

    def create(self, validated_data):
        primary_ids = self.initial_data.get('primary_manager_ids', [])
        secondary_ids = self.initial_data.get('secondary_manager_ids', [])
        instance = super().create(validated_data)

        if primary_ids:
            for emp_id in primary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance,
                    employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.PRIMARY}
                )

        if secondary_ids:
            for emp_id in secondary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance,
                    employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.SECONDARY}
                )

        return instance


class ProjectTaskSerializer(serializers.ModelSerializer):
    assignee_name  = serializers.CharField(source='assignee.full_name', read_only=True, default=None)
    status_label   = serializers.CharField(source='get_status_display', read_only=True)
    project_code   = serializers.CharField(source='project.code', read_only=True)
    project_name   = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model  = ProjectTask
        fields = [
            'id', 'project', 'project_code', 'project_name',
            'title', 'description', 'assignee', 'assignee_name',
            'status', 'status_label', 'start_date', 'end_date',
            'progress', 'order', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


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
        read_only_fields = ['id', 'status']

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
