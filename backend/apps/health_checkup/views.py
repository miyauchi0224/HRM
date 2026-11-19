from datetime import date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsNotCustomer, IsLabor
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.common.utils import fiscal_year_of
from apps.employees.models import Employee
from .models import HealthCheckup
from .serializers import HealthCheckupSerializer


class HealthCheckupViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    健康診断（詳細設計書 7.6）

    本人: 自分の記録を閲覧のみ / 労務・人事・管理者: 全件の閲覧・登録・編集
    ?fiscal_year= / ?employee_id= / ?followup_pending=true で絞り込み
    """
    serializer_class = HealthCheckupSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsNotCustomer()]
        return [IsLabor()]

    def get_queryset(self):
        user = self.request.user
        qs = HealthCheckup.objects.select_related('employee')
        if not user.is_labor:
            qs = qs.filter(employee__user=user)
        params = self.request.query_params
        if params.get('fiscal_year'):
            qs = qs.filter(fiscal_year=params['fiscal_year'])
        if params.get('employee_id') and user.is_labor:
            qs = qs.filter(employee_id=params['employee_id'])
        if params.get('followup_pending') == 'true':
            qs = qs.filter(result__in=HealthCheckup.FOLLOWUP_RESULTS, followup_completed_date__isnull=True)
        return qs

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """GET /api/v1/health-checkups/summary/?fiscal_year=2026 — 受診率・要フォロー件数"""
        if not request.user.is_labor:
            return Response({'error': '労務担当以上の権限が必要です'}, status=status.HTTP_403_FORBIDDEN)
        try:
            fy = int(request.query_params.get('fiscal_year') or fiscal_year_of(date.today()))
        except ValueError:
            return Response({'error': 'fiscal_year は数値で指定してください'}, status=status.HTTP_400_BAD_REQUEST)

        targets = [e for e in Employee.objects.select_related('user').filter(retire_date__isnull=True)
                   if not e.user.is_customer]
        records = list(HealthCheckup.objects.filter(fiscal_year=fy).select_related('employee'))
        checked_ids = {r.employee_id for r in records
                       if r.checkup_type == HealthCheckup.CheckupType.REGULAR and r.checkup_date}

        unchecked = [
            {'employee_id': str(e.id), 'full_name': e.full_name, 'department': e.department}
            for e in targets if e.id not in checked_ids
        ]
        checked = len(targets) - len(unchecked)
        return Response({
            'fiscal_year':             fy,
            'target_count':            len(targets),
            'checked_count':           checked,
            'checkup_rate':            round(checked / len(targets) * 100, 1) if targets else 0,
            'followup_required_count': sum(1 for r in records if r.followup_required),
            'followup_pending_count':  sum(1 for r in records if r.followup_pending),
            'unchecked':               unchecked,
        })
