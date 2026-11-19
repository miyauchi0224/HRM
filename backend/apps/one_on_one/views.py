from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsNotCustomer
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.notifications.models import Notification
from .ai import AISummaryError, summarize_meeting
from .models import OneOnOneMeeting
from .serializers import OneOnOneMeetingSerializer


class OneOnOneMeetingViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    1on1（詳細設計書 7.7）。参加者（上司・部下）だけが閲覧・編集できる。
    ?with=<employee_id> で相手を絞り込み
    """
    serializer_class   = OneOnOneMeetingSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        employee = getattr(self.request.user, 'employee', None)
        if employee is None:
            return OneOnOneMeeting.objects.none()
        qs = OneOnOneMeeting.objects.select_related('manager', 'member').filter(
            Q(manager=employee) | Q(member=employee)
        )
        partner = self.request.query_params.get('with')
        if partner:
            qs = qs.filter(Q(manager_id=partner) | Q(member_id=partner))
        return qs

    def perform_create(self, serializer):
        meeting = serializer.save(created_by=self.request.user)
        me      = self.request.user.employee
        other   = meeting.member if meeting.manager_id == me.id else meeting.manager
        Notification.send(
            user=other.user,
            type_=Notification.NotificationType.ONE_ON_ONE,
            title='1on1 が登録されました',
            message=f'{me.full_name}さんとの1on1：{meeting.scheduled_at:%m/%d %H:%M}（{meeting.duration_minutes}分）',
            related_url='/one-on-one',
        )

    @action(detail=False, methods=['get'], url_path='partners')
    def partners(self, request):
        """GET /api/v1/one-on-one/meetings/partners/ — 1on1 の相手候補（自分の部下・上司）"""
        employee = getattr(request.user, 'employee', None)
        if employee is None:
            return Response({'members': [], 'managers': []})
        row = lambda e: {'id': str(e.id), 'full_name': e.full_name, 'department': e.department}
        return Response({
            'members':  [row(e) for e in employee.subordinates.filter(retire_date__isnull=True)],
            'managers': [row(e) for e in employee.managers.all()],
        })

    @action(detail=True, methods=['post'], url_path='ai-summary')
    def ai_summary(self, request, pk=None):
        """POST /api/v1/one-on-one/meetings/{id}/ai-summary/ — 要約・アクションアイテム・次回アジェンダ案"""
        meeting  = self.get_object()
        previous = OneOnOneMeeting.objects.filter(
            manager=meeting.manager, member=meeting.member,
            scheduled_at__lt=meeting.scheduled_at,
        ).exclude(status=OneOnOneMeeting.Status.CANCELLED).order_by('-scheduled_at').first()
        try:
            result = summarize_meeting(meeting, previous, request.user)
        except AISummaryError as e:
            return Response({'error': str(e)}, status=e.status_code)

        meeting.ai_summary = result['summary']
        meeting.save(update_fields=['ai_summary', 'updated_at'])
        return Response(result)
