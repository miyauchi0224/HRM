import io
import calendar
from datetime import date, datetime, time
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import AttendanceRecord, AttendanceModRequest, Project
from .serializers import (
    AttendanceRecordSerializer, ClockInSerializer, ClockOutSerializer,
    AttendanceModRequestSerializer, ProjectSerializer, AttendanceSummarySerializer
)
from apps.notifications.models import Notification


OVERTIME_WARNING_MINUTES = 40 * 60   # 40時間
OVERTIME_ALERT_MINUTES   = 80 * 60   # 80時間（36協定）


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.filter(is_active=True)
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = AttendanceRecord.objects.select_related('project', 'employee')
        year_month = self.request.query_params.get('year_month')

        # 管理職・人事は部下/全員を参照可
        emp_id = self.request.query_params.get('employee_id')
        if user.is_manager and emp_id:
            qs = qs.filter(employee_id=emp_id)
        else:
            qs = qs.filter(employee__user=user)

        if year_month:
            year, month = year_month.split('-')
            qs = qs.filter(date__year=year, date__month=month)
        return qs.order_by('-date')

    @action(detail=False, methods=['post'], url_path='clock-in')
    def clock_in(self, request):
        """POST /api/v1/attendance/clock-in/"""
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = request.user.employee
        today    = date.today()

        # 当日の記録が既にあればエラー
        if AttendanceRecord.objects.filter(employee=employee, date=today).exists():
            return Response({'error': '本日はすでに出勤打刻済みです'}, status=status.HTTP_409_CONFLICT)

        record = AttendanceRecord.objects.create(
            employee    = employee,
            date        = today,
            clock_in    = timezone.localtime().time(),
            project_id  = serializer.validated_data.get('project_id'),
            note        = serializer.validated_data.get('note', ''),
        )
        return Response(AttendanceRecordSerializer(record).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='clock-out')
    def clock_out(self, request):
        """POST /api/v1/attendance/clock-out/"""
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        employee = request.user.employee
        today    = date.today()
        record   = AttendanceRecord.objects.filter(
            employee=employee, date=today, clock_out__isnull=True
        ).first()

        if not record:
            return Response({'error': '出勤記録がありません'}, status=status.HTTP_404_NOT_FOUND)

        record.clock_out     = timezone.localtime().time()
        record.break_minutes = serializer.validated_data['break_minutes']
        record.status        = AttendanceRecord.Status.CONFIRMED
        record.save()

        # 残業アラートチェック
        self._check_overtime_alert(employee, record)

        return Response(AttendanceRecordSerializer(record).data)

    def _check_overtime_alert(self, employee, record):
        """月間残業時間が閾値を超えたら通知"""
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__year=record.date.year,
            date__month=record.date.month,
        )
        total_overtime = sum(r.overtime_minutes for r in records)
        if total_overtime >= OVERTIME_ALERT_MINUTES:
            Notification.send(
                user=employee.user,
                type_=Notification.NotificationType.OVERTIME_ALERT,
                title='【緊急】残業時間アラート',
                message=f'今月の残業時間が{total_overtime // 60}時間を超えました。36協定の上限に達しています。',
                related_url='/attendance/report',
            )
        elif total_overtime >= OVERTIME_WARNING_MINUTES:
            Notification.send(
                user=employee.user,
                type_=Notification.NotificationType.OVERTIME_ALERT,
                title='残業時間警告',
                message=f'今月の残業時間が{total_overtime // 60}時間になりました。',
                related_url='/attendance/report',
            )

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """GET /api/v1/attendance/summary/?year_month=2026-04"""
        year_month = request.query_params.get('year_month',
                                               date.today().strftime('%Y-%m'))
        year, month = year_month.split('-')
        employee    = request.user.employee
        records     = AttendanceRecord.objects.filter(
            employee=employee, date__year=year, date__month=month,
            clock_in__isnull=False, clock_out__isnull=False,
        )
        total_work     = sum(r.work_minutes for r in records)
        total_overtime = sum(r.overtime_minutes for r in records)
        return Response({
            'year_month':             year_month,
            'total_work_days':        records.count(),
            'total_work_minutes':     total_work,
            'total_overtime_minutes': total_overtime,
            'overtime_alert':         total_overtime >= OVERTIME_ALERT_MINUTES,
        })

    @action(detail=False, methods=['get'], url_path='template')
    def template(self, request):
        """
        GET /api/v1/attendance/template/?year=2026
        年度単位の勤怠テンプレート XLSX をダウンロード
        当日までのデータを既存データから埋め込む
        """
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter

        year = int(request.query_params.get('year', date.today().year))
        emp_id = request.query_params.get('employee_id')
        if emp_id and request.user.is_manager:
            from apps.employees.models import Employee
            employee = Employee.objects.filter(id=emp_id).first()
        else:
            employee = getattr(request.user, 'employee', None)

        if not employee:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        # 既存の勤怠データを取得
        existing = {
            r.date: r
            for r in AttendanceRecord.objects.filter(
                employee=employee,
                date__year=year,
            )
        }

        wb = openpyxl.Workbook()
        # ヘッダースタイル
        header_fill = PatternFill(fill_type='solid', fgColor='2E75B6')
        header_font = Font(color='FFFFFF', bold=True)
        thin_border = Border(
            left=Side(style='thin'), right=Side(style='thin'),
            top=Side(style='thin'), bottom=Side(style='thin'),
        )

        today = date.today()

        for month in range(1, 13):
            ws = wb.create_sheet(title=f'{month}月')
            ws.column_dimensions['A'].width = 12
            ws.column_dimensions['B'].width = 8
            ws.column_dimensions['C'].width = 10
            ws.column_dimensions['D'].width = 10
            ws.column_dimensions['E'].width = 8
            ws.column_dimensions['F'].width = 12
            ws.column_dimensions['G'].width = 20

            # タイトル行
            ws['A1'] = f'{year}年{month}月 勤怠表'
            ws['A1'].font = Font(bold=True, size=12)
            ws['A2'] = f'氏名：{employee.full_name}　社員番号：{employee.employee_number}'

            # ヘッダー行
            headers = ['日付', '曜日', '出勤時刻', '退勤時刻', '休憩(分)', 'プロジェクト', '備考']
            for col, h in enumerate(headers, 1):
                cell = ws.cell(row=3, column=col, value=h)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')
                cell.border = thin_border

            # 日付ごとのデータ
            days_in_month = calendar.monthrange(year, month)[1]
            weekday_names = ['月', '火', '水', '木', '金', '土', '日']
            row = 4
            for day in range(1, days_in_month + 1):
                d = date(year, month, day)
                wd = weekday_names[d.weekday()]
                record = existing.get(d)

                row_data = [
                    d.strftime('%Y/%m/%d'),
                    wd,
                    record.clock_in.strftime('%H:%M') if record and record.clock_in else '',
                    record.clock_out.strftime('%H:%M') if record and record.clock_out else '',
                    record.break_minutes if record else 60,
                    record.project.code if record and record.project else '',
                    record.note if record else '',
                ]
                for col, val in enumerate(row_data, 1):
                    cell = ws.cell(row=row, column=col, value=val)
                    cell.border = thin_border
                    if d.weekday() == 5:  # 土曜
                        cell.fill = PatternFill(fill_type='solid', fgColor='DDEEFF')
                    elif d.weekday() == 6:  # 日曜
                        cell.fill = PatternFill(fill_type='solid', fgColor='FFDDDD')
                    # 未来日は空欄で保護しない（ユーザーが入力可能）
                row += 1

        # デフォルトシートを削除
        if 'Sheet' in wb.sheetnames:
            del wb['Sheet']

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f'attendance_{year}_{employee.employee_number}.xlsx'
        response = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=False, methods=['post'], url_path='upload',
            parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        POST /api/v1/attendance/upload/
        XLSX をアップロードして勤怠データを一括登録・更新
        """
        import openpyxl

        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'ファイルが指定されていません'}, status=status.HTTP_400_BAD_REQUEST)

        emp_id = request.data.get('employee_id')
        if emp_id and request.user.is_manager:
            from apps.employees.models import Employee
            employee = Employee.objects.filter(id=emp_id).first()
        else:
            employee = getattr(request.user, 'employee', None)

        if not employee:
            return Response({'error': '社員情報が見つかりません'}, status=status.HTTP_404_NOT_FOUND)

        try:
            wb = openpyxl.load_workbook(file, data_only=True)
        except Exception:
            return Response({'error': '無効なXLSXファイルです'}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        updated = 0
        errors  = []

        for sheet in wb.worksheets:
            # 4行目以降がデータ行（1:タイトル, 2:氏名, 3:ヘッダー）
            for row in sheet.iter_rows(min_row=4, values_only=True):
                try:
                    date_val, _, clock_in_str, clock_out_str, break_min, project_code, note = row[:7]
                    if not date_val:
                        continue

                    # 日付パース
                    if isinstance(date_val, datetime):
                        d = date_val.date()
                    elif isinstance(date_val, date):
                        d = date_val
                    else:
                        d = datetime.strptime(str(date_val), '%Y/%m/%d').date()

                    # 時刻パース
                    def parse_time(val):
                        if not val:
                            return None
                        if isinstance(val, time):
                            return val
                        if isinstance(val, datetime):
                            return val.time()
                        s = str(val).strip()
                        if ':' in s:
                            parts = s.split(':')
                            return time(int(parts[0]), int(parts[1]))
                        return None

                    ci = parse_time(clock_in_str)
                    co = parse_time(clock_out_str)
                    bm = int(break_min) if break_min else 60

                    # プロジェクト解決
                    project = None
                    if project_code:
                        project = Project.objects.filter(code=str(project_code).strip()).first()

                    obj, is_created = AttendanceRecord.objects.update_or_create(
                        employee=employee,
                        date=d,
                        defaults=dict(
                            clock_in=ci,
                            clock_out=co,
                            break_minutes=bm,
                            project=project,
                            note=str(note) if note else '',
                            status=AttendanceRecord.Status.CONFIRMED if ci and co else AttendanceRecord.Status.DRAFT,
                        )
                    )
                    if is_created:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f'シート「{sheet.title}」: {str(e)}')

        return Response({'created': created, 'updated': updated, 'errors': errors})


class AttendanceModRequestViewSet(viewsets.ModelViewSet):
    serializer_class   = AttendanceModRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_manager:
            return AttendanceModRequest.objects.all()
        return AttendanceModRequest.objects.filter(applicant__user=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user.employee)
        employee = self.request.user.employee
        for manager in employee.managers.all():
            Notification.send(
                user=manager.user,
                type_=Notification.NotificationType.ATTENDANCE_MOD,
                title='打刻修正申請',
                message=f'{employee.full_name}さんから打刻修正申請が届きました。',
                related_url='/attendance/modification',
            )

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/v1/attendance/modification-requests/{id}/approve/"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        mod = self.get_object()
        if mod.status != AttendanceModRequest.Status.PENDING:
            return Response({'error': '申請中のものだけ承認できます'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = request.data.get('action', 'approve')
        if action_type == 'approve':
            mod.status      = AttendanceModRequest.Status.APPROVED
            mod.approver    = request.user.employee
            mod.approved_at = timezone.now()
            mod.save()
            # 勤怠記録に反映
            mod.attendance.clock_in  = mod.requested_clock_in
            mod.attendance.clock_out = mod.requested_clock_out
            mod.attendance.status    = AttendanceRecord.Status.MODIFIED
            mod.attendance.save()
            msg = '打刻修正申請が承認されました'
        else:
            mod.status = AttendanceModRequest.Status.REJECTED
            mod.save()
            msg = '打刻修正申請が却下されました'

        Notification.send(
            user=mod.applicant.user,
            type_=Notification.NotificationType.ATTENDANCE_MOD,
            title=msg,
            message=msg,
            related_url='/attendance/calendar',
        )
        return Response(AttendanceModRequestSerializer(mod).data)
