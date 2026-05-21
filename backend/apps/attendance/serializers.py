"""
attendance/serializers.py

プロジェクト・タスク・勤怠関連のシリアライザー定義。

設計ポイント:
  - ProjectSerializer は SerializerMethodField（読み取り専用）でレスポンスを返し、
    create/update 内で self.initial_data から primary_manager_ids を取り出して
    ProjectManager 中間テーブルを操作する（M2M 管理者パターン）。
  - AttendanceRecordSerializer は project_records のネスト書き込みに対応。
    validate() でプロジェクト合計分数 ≦ 労働時間を検証する。
"""
from rest_framework import serializers
from .models import (
    AttendanceRecord, AttendanceProjectRecord, AttendanceModRequest,
    Project, ProjectTask, ProjectManager,
)
from datetime import date


# ─── プロジェクト関連 ──────────────────────────────────────────────────────

class ManagerDetailSerializer(serializers.Serializer):
    """管理者の id / full_name を返す軽量シリアライザー"""
    id        = serializers.UUIDField()
    full_name = serializers.CharField()


class ProjectSerializer(serializers.ModelSerializer):
    """
    プロジェクトのシリアライザー。

    管理者は ProjectManager 中間テーブルで管理（M2M）。
    読み取り: SerializerMethodField で primary_managers / secondary_managers を返す。
    書き込み: create / update で self.initial_data から *_ids リストを受け取り
              ProjectManager レコードを洗い替えする。
    """

    # 主管理者・従管理者のオブジェクトリスト（画面表示用）
    primary_managers   = serializers.SerializerMethodField()
    secondary_managers = serializers.SerializerMethodField()

    # 主管理者・従管理者の ID リスト（フロントのフォーム初期値に使用）
    primary_manager_ids   = serializers.SerializerMethodField()
    secondary_manager_ids = serializers.SerializerMethodField()

    # タスク件数（一覧カードに表示）
    task_count = serializers.SerializerMethodField()

    # 後方互換: 旧 manager FK 廃止後も一部 UI が参照するため主管理者1件目を返す
    manager      = serializers.SerializerMethodField()
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model  = Project
        fields = [
            'id', 'code', 'name', 'description',
            'manager', 'manager_name',
            'primary_managers', 'secondary_managers',
            'primary_manager_ids', 'secondary_manager_ids',
            'is_active', 'start_date', 'end_date', 'task_count',
        ]

    # ── SerializerMethodField 実装 ──

    def get_primary_managers(self, obj):
        """主管理者リストを [{id, full_name}] 形式で返す"""
        pms = obj.project_managers.filter(
            role=ProjectManager.Role.PRIMARY
        ).select_related('employee')
        return [{'id': str(pm.employee.id), 'full_name': pm.employee.full_name} for pm in pms]

    def get_secondary_managers(self, obj):
        """従管理者リストを [{id, full_name}] 形式で返す"""
        pms = obj.project_managers.filter(
            role=ProjectManager.Role.SECONDARY
        ).select_related('employee')
        return [{'id': str(pm.employee.id), 'full_name': pm.employee.full_name} for pm in pms]

    def get_primary_manager_ids(self, obj):
        return [str(pm.employee.id)
                for pm in obj.project_managers.filter(role=ProjectManager.Role.PRIMARY)]

    def get_secondary_manager_ids(self, obj):
        return [str(pm.employee.id)
                for pm in obj.project_managers.filter(role=ProjectManager.Role.SECONDARY)]

    def get_manager(self, obj):
        """後方互換: 主管理者1件目の ID を返す"""
        pm = obj.project_managers.filter(role=ProjectManager.Role.PRIMARY).first()
        return str(pm.employee.id) if pm else None

    def get_manager_name(self, obj):
        """後方互換: 主管理者1件目の氏名を返す"""
        pm = obj.project_managers.filter(
            role=ProjectManager.Role.PRIMARY
        ).select_related('employee').first()
        return pm.employee.full_name if pm else None

    def get_task_count(self, obj):
        return obj.tasks.count()

    # ── 書き込み処理 ──

    def create(self, validated_data):
        """
        プロジェクト作成後、*_ids を ProjectManager 中間テーブルに登録する。

        SerializerMethodField は read_only のため validated_data に含まれない。
        代わりに self.initial_data（生リクエストデータ）から取得する。
        """
        primary_ids   = self.initial_data.get('primary_manager_ids', [])
        secondary_ids = self.initial_data.get('secondary_manager_ids', [])

        instance = super().create(validated_data)

        for emp_id in primary_ids:
            ProjectManager.objects.get_or_create(
                project=instance, employee_id=emp_id,
                defaults={'role': ProjectManager.Role.PRIMARY},
            )
        for emp_id in secondary_ids:
            ProjectManager.objects.get_or_create(
                project=instance, employee_id=emp_id,
                defaults={'role': ProjectManager.Role.SECONDARY},
            )
        return instance

    def update(self, instance, validated_data):
        """
        プロジェクト更新時、*_ids が送られた場合は既存の
        ProjectManager を削除して再登録する（洗い替え）。
        None の場合（キー未送信）はそのまま維持する。
        """
        primary_ids   = self.initial_data.get('primary_manager_ids',   None)
        secondary_ids = self.initial_data.get('secondary_manager_ids', None)

        instance = super().update(instance, validated_data)

        if primary_ids is not None:
            # 洗い替え: 既存の主管理者を全削除 → 再登録
            instance.project_managers.filter(role=ProjectManager.Role.PRIMARY).delete()
            for emp_id in primary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance, employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.PRIMARY},
                )

        if secondary_ids is not None:
            # 洗い替え: 既存の従管理者を全削除 → 再登録
            instance.project_managers.filter(role=ProjectManager.Role.SECONDARY).delete()
            for emp_id in secondary_ids:
                ProjectManager.objects.get_or_create(
                    project=instance, employee_id=emp_id,
                    defaults={'role': ProjectManager.Role.SECONDARY},
                )

        return instance


class ProjectTaskSerializer(serializers.ModelSerializer):
    """プロジェクトタスクのシリアライザー"""
    assignee_name = serializers.CharField(source='assignee.full_name', read_only=True, default=None)
    status_label  = serializers.CharField(source='get_status_display', read_only=True)
    project_code  = serializers.CharField(source='project.code', read_only=True)
    project_name  = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model  = ProjectTask
        fields = [
            'id', 'project', 'project_code', 'project_name',
            'title', 'description', 'assignee', 'assignee_name',
            'status', 'status_label', 'start_date', 'end_date',
            'progress', 'order', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ─── 勤怠関連 ─────────────────────────────────────────────────────────────

class AttendanceProjectRecordSerializer(serializers.ModelSerializer):
    """勤怠レコードに紐づくプロジェクト別作業時間"""
    project_code = serializers.CharField(source='project.code', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model  = AttendanceProjectRecord
        fields = ['id', 'project', 'project_code', 'project_name', 'minutes']


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    勤怠レコード（1社員 × 1日）シリアライザー。

    project_records のネスト書き込みに対応。
    validate() でプロジェクト合計分数 ≦ 実労働時間を検証する。
    """
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
        """プロジェクト作業合計が実労働時間を超えないことを検証"""
        project_records = data.get('project_records')
        if not project_records:
            return data

        # 更新中の値 or 既存値を使って実労働時間を計算
        clock_in  = data.get('clock_in')  or getattr(self.instance, 'clock_in',  None)
        clock_out = data.get('clock_out') or getattr(self.instance, 'clock_out', None)
        break_min = data.get('break_minutes') or getattr(self.instance, 'break_minutes', 60)

        if clock_in and clock_out:
            from datetime import datetime, date as d
            ci = datetime.combine(d.today(), clock_in)
            co = datetime.combine(d.today(), clock_out)
            work_min  = max(0, int((co - ci).total_seconds() / 60) - break_min)
            total_pj  = sum(pr['minutes'] for pr in project_records)
            if total_pj > work_min:
                raise serializers.ValidationError(
                    f'プロジェクト合計（{total_pj}分）が労働時間（{work_min}分）を超えています。'
                )
        return data

    def update(self, instance, validated_data):
        """project_records は一旦全削除して再登録（洗い替え）"""
        project_records_data = validated_data.pop('project_records', None)
        instance = super().update(instance, validated_data)
        if project_records_data is not None:
            instance.project_records.all().delete()
            for pr in project_records_data:
                AttendanceProjectRecord.objects.create(attendance=instance, **pr)
        return instance


class ClockInSerializer(serializers.Serializer):
    """出勤打刻リクエスト用シリアライザー"""
    note = serializers.CharField(required=False, allow_blank=True)


class ClockOutSerializer(serializers.Serializer):
    """退勤打刻リクエスト用シリアライザー（休憩時間を受け取る）"""
    break_minutes = serializers.IntegerField(default=60, min_value=0)


class AttendanceModRequestSerializer(serializers.ModelSerializer):
    """打刻修正申請シリアライザー"""
    applicant_name = serializers.CharField(source='applicant.full_name', read_only=True)
    # 申請対象日を日付として返す（勤怠レコード経由）
    date = serializers.DateField(source='attendance.date', read_only=True)

    class Meta:
        model  = AttendanceModRequest
        fields = [
            'id', 'attendance', 'date', 'applicant_name',
            'requested_clock_in', 'requested_clock_out',
            'reason', 'status', 'approved_at', 'created_at',
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'created_at']


class AttendanceSummarySerializer(serializers.Serializer):
    """月次勤怠サマリー（集計値）シリアライザー"""
    year_month             = serializers.CharField()
    total_work_days        = serializers.IntegerField()
    total_work_minutes     = serializers.IntegerField()
    total_overtime_minutes = serializers.IntegerField()
    overtime_alert         = serializers.BooleanField()  # 36協定超過フラグ
