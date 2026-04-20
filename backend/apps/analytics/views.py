from datetime import date, timedelta
from collections import defaultdict
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.accounts.permissions import IsHR

from apps.attendance.models import AttendanceRecord
from apps.leave.models import LeaveBalance
from apps.expense.models import ExpenseRequest
from apps.employees.models import Employee


class AttendanceTrendView(APIView):
    """月別平均出勤日数トレンド（過去6か月）"""
    permission_classes = [IsHR]

    def get(self, request):
        today = date.today()
        six_months_ago = today - timedelta(days=180)
        data = (
            AttendanceRecord.objects
            .filter(date__gte=six_months_ago, clock_in__isnull=False)
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(record_count=Count('id'), employee_count=Count('employee', distinct=True))
            .order_by('month')
        )
        result = []
        for row in data:
            avg_days = round(row['record_count'] / max(row['employee_count'], 1), 1)
            result.append({
                'month': row['month'].strftime('%Y-%m') if row['month'] else None,
                'avg_attendance_days': avg_days,
                'total_records': row['record_count'],
                'employee_count': row['employee_count'],
            })
        return Response(result)


class LeaveUsageView(APIView):
    """有給消化率"""
    permission_classes = [IsHR]

    def get(self, request):
        year = int(request.query_params.get('year', date.today().year))
        balances = LeaveBalance.objects.filter(fiscal_year=year).select_related('employee')
        data = []
        for b in balances:
            total = b.granted_days + b.carried_over
            used = b.used_days
            pct = round(used / total * 100, 1) if total > 0 else 0
            data.append({
                'employee_id': str(b.employee.id),
                'employee_name': b.employee.full_name,
                'granted': float(total),
                'used': float(used),
                'remaining': float(b.remaining_days),
                'usage_pct': pct,
            })
        return Response(data)


class HeadcountView(APIView):
    """ロール別人員数"""
    permission_classes = [IsHR]

    def get(self, request):
        from apps.accounts.models import User
        by_role = (
            User.objects
            .values('role')
            .annotate(count=Count('id'))
            .order_by('role')
        )
        total = Employee.objects.count()
        return Response({'total': total, 'by_role': list(by_role)})


class ExpenseSummaryView(APIView):
    """月別経費集計"""
    permission_classes = [IsHR]

    def get(self, request):
        today = date.today()
        six_months_ago = today - timedelta(days=180)
        data = (
            ExpenseRequest.objects
            .filter(expense_date__gte=six_months_ago, status=ExpenseRequest.Status.APPROVED)
            .annotate(month=TruncMonth('expense_date'))
            .values('month', 'expense_type')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('month')
        )
        result = []
        for row in data:
            result.append({
                'month': row['month'].strftime('%Y-%m') if row['month'] else None,
                'expense_type': row['expense_type'],
                'total': row['total'],
                'count': row['count'],
            })
        return Response(result)


class OvertimeRankingView(APIView):
    """当月の出勤記録数ランキング"""
    permission_classes = [IsHR]

    def get(self, request):
        today = date.today()
        data = (
            AttendanceRecord.objects
            .filter(date__year=today.year, date__month=today.month, clock_in__isnull=False)
            .values('employee__id', 'employee__full_name')
            .annotate(attendance_days=Count('id'))
            .order_by('-attendance_days')[:20]
        )
        return Response(list(data))
