from datetime import timedelta

from django.conf import settings
from rest_framework import serializers

from .models import LeaveBalance, LeaveGrant, LeaveRequest


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
    holiday_work_date = serializers.DateField(source='holiday_work.date', read_only=True, default=None)

    class Meta:
        model  = LeaveRequest
        fields = [
            'id', 'leave_type', 'start_date', 'end_date', 'days',
            'reason', 'status', 'approved_at', 'created_at',
            'employee_name', 'approver_name', 'holiday_work', 'holiday_work_date',
        ]
        read_only_fields = ['id', 'status', 'approved_at', 'created_at',
                            'employee_name', 'approver_name', 'holiday_work_date']

    def _resolved(self, data, field):
        """部分更新（PATCH）では送られていない項目を既存の値で補う"""
        if field in data:
            return data[field]
        return getattr(self.instance, field, None) if self.instance is not None else None

    def validate(self, data):
        start_date = self._resolved(data, 'start_date')
        end_date   = self._resolved(data, 'end_date')
        leave_type = self._resolved(data, 'leave_type')
        days       = self._resolved(data, 'days')

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError('開始日は終了日以前である必要があります')

        if days is not None:
            if days <= 0:
                raise serializers.ValidationError({'days': '日数は 0 より大きい値を入力してください'})
            if start_date and end_date and days > (end_date - start_date).days + 1:
                raise serializers.ValidationError({'days': '日数が申請期間の日数を超えています'})

        if leave_type == LeaveRequest.LeaveType.COMPENSATORY:
            if 'holiday_work' not in data and self.instance is not None:
                data['holiday_work'] = self.instance.holiday_work
            self._validate_compensatory(data, start_date)
        else:
            data['holiday_work'] = None

        if leave_type == LeaveRequest.LeaveType.ANNUAL and start_date and days is not None:
            self._validate_annual_balance(start_date, days)
        return data

    def _validate_annual_balance(self, start_date, days):
        """有給: 申請中の分も含めて、残日数を超えて申請できないようにする"""
        from .services import available_annual_days

        employee = self.instance.employee if self.instance is not None else getattr(
            getattr(self.context.get('request'), 'user', None), 'employee', None)
        if employee is None:
            return
        available = available_annual_days(
            employee, start_date, exclude_pk=self.instance.pk if self.instance is not None else None,
        )
        if days > available:
            raise serializers.ValidationError(
                {'days': f'有給の残日数が足りません（申請可能: {available} 日）'}
            )

    def _validate_compensatory(self, data, start_date):
        """代休: 本人の退勤済みの休日出勤に1対1で紐づくこと（詳細設計書 7.2）"""
        from apps.attendance.models import AttendanceRecord

        hw = data.get('holiday_work')
        if hw is None:
            raise serializers.ValidationError({'holiday_work': '代休の元になる休日出勤を選んでください'})

        request  = self.context.get('request')
        employee = getattr(getattr(request, 'user', None), 'employee', None)
        if employee is None or hw.employee_id != employee.id:
            raise serializers.ValidationError({'holiday_work': '自分の休日出勤のみ選べます'})
        if hw.day_type == AttendanceRecord.DayType.WEEKDAY:
            raise serializers.ValidationError({'holiday_work': '休日（所定休日・法定休日）の勤務のみ選べます'})
        if hw.clock_out is None:
            raise serializers.ValidationError({'holiday_work': '退勤していない勤務は選べません'})

        used = LeaveRequest.objects.filter(
            holiday_work=hw,
            status__in=(LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED),
        )
        if self.instance is not None:
            used = used.exclude(pk=self.instance.pk)
        if used.exists():
            raise serializers.ValidationError({'holiday_work': 'この休日出勤の代休はすでに申請されています'})

        limit = hw.date + timedelta(days=settings.COMPENSATORY_LEAVE_VALID_DAYS)
        if not (hw.date < start_date <= limit):
            raise serializers.ValidationError(
                {'start_date': f'代休は休日出勤日の翌日から {limit} までに取得してください'}
            )


class LeaveGrantSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model  = LeaveGrant
        fields = ['id', 'employee', 'employee_name', 'grant_date', 'days', 'expires_on',
                  'source', 'note', 'created_at']
        read_only_fields = ['id', 'expires_on', 'source', 'created_at']

    def validate_days(self, value):
        if value <= 0 or value > 40:
            raise serializers.ValidationError('付与日数は 0.5〜40 日で入力してください')
        return value

    def validate(self, data):
        if LeaveGrant.all_objects.filter(employee=data['employee'], grant_date=data['grant_date']).exists():
            raise serializers.ValidationError({'grant_date': 'この社員にはこの日付の付与がすでにあります'})
        return data
