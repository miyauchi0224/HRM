import io
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone

from .models import SalaryGrade, Allowance, EmployeeAllowance, Payslip
from .serializers import (
    SalaryGradeSerializer, AllowanceSerializer,
    EmployeeAllowanceSerializer, PayslipSerializer
)
from apps.employees.models import Employee
from apps.attendance.models import AttendanceRecord


# ── 社会保険・税率定数（概算） ─────────────────────────────────────────
HEALTH_INSURANCE_RATE     = Decimal('0.0500')   # 健康保険 5.00%（労働者負担）
PENSION_RATE              = Decimal('0.0915')   # 厚生年金 9.15%
EMPLOYMENT_INSURANCE_RATE = Decimal('0.006')    # 雇用保険 0.6%
OVERTIME_RATE             = Decimal('1.25')     # 残業割増率


class IsHR(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_hr


class SalaryGradeViewSet(viewsets.ModelViewSet):
    queryset           = SalaryGrade.objects.all()
    serializer_class   = SalaryGradeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsAuthenticated()]


class AllowanceViewSet(viewsets.ModelViewSet):
    queryset           = Allowance.objects.all()
    serializer_class   = AllowanceSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [IsHR()]
        return [IsAuthenticated()]


class EmployeeAllowanceViewSet(viewsets.ModelViewSet):
    serializer_class   = EmployeeAllowanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_hr:
            emp_id = self.request.query_params.get('employee_id')
            if emp_id:
                return EmployeeAllowance.objects.filter(employee_id=emp_id)
            return EmployeeAllowance.objects.all()
        return EmployeeAllowance.objects.filter(employee__user=user)


class PayslipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = PayslipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_hr:
            emp_id = self.request.query_params.get('employee_id')
            qs = Payslip.objects.select_related('employee')
            if emp_id:
                return qs.filter(employee_id=emp_id)
            return qs
        return Payslip.objects.filter(employee__user=user)

    @action(detail=False, methods=['post'], url_path='calculate', permission_classes=[IsHR])
    def calculate(self, request):
        """
        POST /api/v1/salary/payslips/calculate/
        Body: { "year": 2026, "month": 4, "employee_id": "uuid" (optional) }
        指定月の給与を計算して Payslip を生成（または更新）
        """
        year  = request.data.get('year')
        month = request.data.get('month')
        if not year or not month:
            return Response({'error': 'year と month は必須です'}, status=status.HTTP_400_BAD_REQUEST)

        emp_id    = request.data.get('employee_id')
        employees = Employee.objects.all()
        if emp_id:
            employees = employees.filter(id=emp_id)

        results = []
        for emp in employees:
            payslip = _calculate_payslip(emp, int(year), int(month))
            results.append(PayslipSerializer(payslip).data)

        return Response({'calculated': len(results), 'payslips': results})

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        GET /api/v1/salary/payslips/{id}/download/
        給与明細を XLSX 形式でダウンロード
        """
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        import io

        payslip = self.get_object()
        # 権限チェック：自分のまたは人事のみ
        if not request.user.is_hr and payslip.employee.user != request.user:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = '給与明細'

        # ヘッダー
        ws['A1'] = '給与明細書'
        ws['A1'].font = Font(bold=True, size=14)
        ws['A2'] = f'{payslip.year}年{payslip.month}月分'
        ws['A3'] = f'氏名：{payslip.employee.full_name}'
        ws['A4'] = f'社員番号：{payslip.employee.employee_number}'

        ws.append([])
        # 支給
        ws.append(['【支給】', '', '【控除】', ''])
        ws.append(['基本給',          payslip.base_salary,      '健康保険料',       payslip.health_insurance])
        ws.append(['手当合計',         payslip.total_allowances, '厚生年金',         payslip.pension])
        ws.append(['残業手当',         payslip.overtime_pay,     '雇用保険料',       payslip.employment_insurance])
        ws.append(['',                '',                       '所得税',           payslip.income_tax])
        ws.append(['',                '',                       '住民税',           payslip.resident_tax])
        ws.append([])
        ws.append(['支給合計',         payslip.gross_salary,     '控除合計',         payslip.total_deductions])
        ws.append([])
        ws.append(['差引支給額',        payslip.net_salary])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        filename = f'payslip_{payslip.year}{payslip.month:02d}_{payslip.employee.employee_number}.xlsx'
        response = HttpResponse(
            buf.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def _calculate_payslip(employee: Employee, year: int, month: int) -> Payslip:
    """給与計算ロジック"""
    from datetime import date

    # 等級から基本給を取得
    today = date(year, month, 1)
    grade_obj = SalaryGrade.objects.filter(
        grade=employee.grade,
        valid_from__lte=today,
        valid_to__isnull=True,
    ).first()
    # 有効期限なしが無い場合は、valid_to が今日以降のものを取得
    if not grade_obj:
        grade_obj = SalaryGrade.objects.filter(
            grade=employee.grade,
            valid_from__lte=today,
            valid_to__gte=today,
        ).first()
    if not grade_obj:
        grade_obj = SalaryGrade.objects.filter(grade=employee.grade).order_by('-valid_from').first()

    base_salary = grade_obj.base_salary if grade_obj else 0

    # 手当合計（有効期限なし、または有効期限が計算対象月以降のもの）
    from django.db.models import Q
    allowances = EmployeeAllowance.objects.filter(
        employee=employee,
        valid_from__lte=today,
    ).filter(
        Q(valid_to__isnull=True) | Q(valid_to__gte=today)
    ).select_related('allowance')
    total_allowances = sum(
        (a.amount if a.amount is not None else a.allowance.amount)
        for a in allowances
    )

    # 残業手当（時給換算: 基本給÷所定労働時間160h × 残業時間 × 1.25）
    records = AttendanceRecord.objects.filter(
        employee=employee, date__year=year, date__month=month,
        clock_out__isnull=False,
    )
    total_overtime_min = sum(r.overtime_minutes for r in records)
    hourly_rate        = Decimal(str(base_salary)) / 160
    overtime_pay       = int(hourly_rate * Decimal(str(total_overtime_min / 60)) * OVERTIME_RATE)

    # 支給合計
    gross_salary = base_salary + total_allowances + overtime_pay

    # 社会保険・税計算（概算）
    health_insurance     = int(Decimal(str(gross_salary)) * HEALTH_INSURANCE_RATE)
    pension              = int(Decimal(str(gross_salary)) * PENSION_RATE)
    employment_insurance = int(Decimal(str(gross_salary)) * EMPLOYMENT_INSURANCE_RATE)
    # 所得税（簡易）: 課税所得に対して概算5%
    taxable              = gross_salary - health_insurance - pension - employment_insurance
    income_tax           = int(Decimal(str(max(0, taxable))) * Decimal('0.05'))
    resident_tax         = 0  # 住民税は別途設定
    total_deductions     = health_insurance + pension + employment_insurance + income_tax + resident_tax
    net_salary           = gross_salary - total_deductions

    payslip, _ = Payslip.objects.update_or_create(
        employee=employee, year=year, month=month,
        defaults=dict(
            base_salary=base_salary,
            total_allowances=total_allowances,
            overtime_pay=overtime_pay,
            gross_salary=gross_salary,
            health_insurance=health_insurance,
            pension=pension,
            employment_insurance=employment_insurance,
            income_tax=income_tax,
            resident_tax=resident_tax,
            total_deductions=total_deductions,
            net_salary=net_salary,
            status=Payslip.Status.DRAFT,
        )
    )
    return payslip
