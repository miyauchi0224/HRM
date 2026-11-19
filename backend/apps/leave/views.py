from datetime import date

from django.db.models import F, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsNotCustomer
from apps.approval.delegation import (
    delegated_applicant_filter, is_delegate_for_applicant, notify_approvers,
)
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.common.utils import fiscal_year_of
from apps.notifications.models import Notification
from .models import LeaveBalance, LeaveGrant, LeaveRequest
from .serializers import LeaveBalanceSerializer, LeaveGrantSerializer, LeaveRequestSerializer
from . import services


class LeaveBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class   = LeaveBalanceSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        if user.is_supervisor:
            emp_id = self.request.query_params.get('employee_id')
            if emp_id:
                return LeaveBalance.objects.filter(employee_id=emp_id)
            return LeaveBalance.objects.all()
        return LeaveBalance.objects.filter(employee__user=user)


class LeaveRequestViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class   = LeaveRequestSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = LeaveRequest.objects.select_related('employee', 'approver', 'holiday_work')
        if user.is_supervisor:
            return qs.all()
        # 自分の申請 ＋ 代理人として承認できる申請
        employee = getattr(user, 'employee', None)
        return qs.filter(
            Q(employee__user=user) | delegated_applicant_filter(employee, 'employee')
        ).distinct()

    def perform_create(self, serializer):
        employee = self.request.user.employee
        req = serializer.save(employee=employee)
        # 上司（＋代理人）へ通知
        notify_approvers(
            list(employee.managers.select_related('user')),
            type_=Notification.NotificationType.LEAVE_REQUEST,
            title='休暇申請',
            message=f'{employee.full_name}さんから休暇申請が届きました（{req.start_date}〜{req.end_date}）',
            related_url='/leave',
        )

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """PATCH /api/v1/leave/requests/{id}/approve/"""
        actor = getattr(request.user, 'employee', None)
        if not request.user.is_supervisor:
            req = LeaveRequest.objects.filter(pk=pk).select_related('employee').first()
            if req is None or not is_delegate_for_applicant(actor, req.employee):
                return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        req = self.get_object()
        if req.status != LeaveRequest.Status.PENDING:
            return Response({'error': '申請中の記録のみ操作できます'}, status=status.HTTP_400_BAD_REQUEST)

        action_type = request.data.get('action', 'approve')
        if action_type == 'approve':
            req.status      = LeaveRequest.Status.APPROVED
            req.approver    = actor
            req.approved_at = timezone.now()
            req.save()
            # 有給の場合は残日数を更新
            if req.leave_type == LeaveRequest.LeaveType.ANNUAL:
                LeaveBalance.objects.filter(
                    employee=req.employee, fiscal_year=fiscal_year_of(req.start_date)
                ).update(used_days=F('used_days') + req.days)
            msg = '休暇申請が承認されました'
        else:
            req.status = LeaveRequest.Status.REJECTED
            req.save()
            msg = '休暇申請が却下されました'

        Notification.send(
            user=req.employee.user,
            type_=Notification.NotificationType.LEAVE_REQUEST,
            title=msg,
            message=f'{req.start_date}〜{req.end_date}の休暇申請が{"承認" if action_type == "approve" else "却下"}されました',
            related_url='/leave',
        )
        return Response(LeaveRequestSerializer(req).data)

    @action(detail=True, methods=['patch'], url_path='cancel')
    def cancel(self, request, pk=None):
        """PATCH /api/v1/leave/requests/{id}/cancel/"""
        req = self.get_object()
        if req.employee.user != request.user:
            return Response({'error': '自分の申請のみ取り消せます'}, status=status.HTTP_403_FORBIDDEN)
        if req.status not in (LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED):
            return Response({'error': 'この申請は取り消せません'}, status=status.HTTP_400_BAD_REQUEST)

        # 承認済みで有給の場合は残日数を戻す
        if req.status == LeaveRequest.Status.APPROVED and req.leave_type == LeaveRequest.LeaveType.ANNUAL:
            LeaveBalance.objects.filter(
                employee=req.employee, fiscal_year=fiscal_year_of(req.start_date)
            ).update(used_days=F('used_days') - req.days)

        req.status = LeaveRequest.Status.CANCELLED
        req.save()
        return Response(LeaveRequestSerializer(req).data)


class LeaveGrantViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    有給付与履歴（詳細設計書 7.2）

    GET    /grants/                       本人の履歴（上司以上は ?employee_id=）
    POST   /grants/                       手動付与（人事）
    DELETE /grants/{id}/                  付与の取り消し（人事。残高からも差し引く）
    GET    /grants/obligation/            自分の年5日取得の状況
    GET    /grants/obligation-summary/    社員ごとの年5日取得の状況（上司・労務・人事）
    """
    serializer_class   = LeaveGrantSerializer
    permission_classes = [IsNotCustomer]
    http_method_names  = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        user = self.request.user
        qs = LeaveGrant.objects.select_related('employee')
        emp_id = self.request.query_params.get('employee_id')
        if user.is_supervisor and emp_id:
            return qs.filter(employee_id=emp_id)
        if user.is_hr and self.action == 'destroy':
            return qs.all()
        return qs.filter(employee__user=user)

    def create(self, request, *args, **kwargs):
        if not request.user.is_hr:
            return Response({'error': '人事担当以上の権限が必要です'}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data
        grant = services.record_grant(d['employee'], d['grant_date'], d['days'],
                                      source=LeaveGrant.Source.MANUAL, note=d.get('note', ''))
        return Response(LeaveGrantSerializer(grant).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_hr:
            return Response({'error': '人事担当以上の権限が必要です'}, status=status.HTTP_403_FORBIDDEN)
        grant = self.get_object()
        LeaveBalance.objects.filter(
            employee=grant.employee, fiscal_year=fiscal_year_of(grant.grant_date),
        ).update(granted_days=F('granted_days') - grant.days)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='obligation')
    def obligation(self, request):
        employee = getattr(request.user, 'employee', None)
        if employee is None:
            return Response({'error': '社員情報が登録されていません'}, status=status.HTTP_404_NOT_FOUND)
        grant = services.current_obligation_grant(employee, date.today())
        if grant is None:
            return Response({'status': 'not_applicable'})
        return Response(services.obligation_status(grant, date.today()))

    @action(detail=False, methods=['get'], url_path='obligation-summary')
    def obligation_summary(self, request):
        user = request.user
        if not (user.is_labor or user.is_supervisor):
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)

        today = date.today()
        grants = LeaveGrant.objects.filter(
            days__gte=services.OBLIGATION_MIN_GRANT,
            grant_date__lte=today,
            grant_date__gt=services.add_years(today, -1),
        ).select_related('employee')
        # 労務・人事は全社員、上司は自分の部下のみ
        if not user.is_labor:
            employee = getattr(user, 'employee', None)
            grants = grants.filter(employee__managers=employee)

        latest = {}
        for g in grants.order_by('employee_id', '-grant_date'):
            latest.setdefault(g.employee_id, g)
        rows = [services.obligation_status(g, today) for g in latest.values()]
        order = {'overdue': 0, 'warning': 1, 'ok': 2}
        rows.sort(key=lambda r: (order[r['status']], r['days_until_deadline']))
        return Response(rows)
