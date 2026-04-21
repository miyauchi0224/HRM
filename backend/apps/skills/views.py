from datetime import date, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsNotCustomer
from rest_framework.response import Response

from .models import Skill
from .serializers import SkillSerializer
from apps.notifications.models import Notification
from apps.common.mixins import SoftDeleteViewSetMixin


class SkillViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class   = SkillSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs   = Skill.objects.select_related('employee')
        if user.is_manager:
            emp_id = self.request.query_params.get('employee_id')
            if emp_id:
                return qs.filter(employee_id=emp_id)
            return qs
        return qs.filter(employee__user=user)

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=False, methods=['get'], url_path='expiry-alert')
    def expiry_alert(self, request):
        """
        GET /api/v1/skills/expiry-alert/
        有効期限が90日以内のスキル・資格一覧を返す
        """
        threshold = date.today() + timedelta(days=90)
        qs = Skill.objects.filter(
            expiry_date__isnull=False,
            expiry_date__lte=threshold,
            expiry_date__gte=date.today(),
        )
        if not request.user.is_manager:
            qs = qs.filter(employee__user=request.user)

        # 期限切れ間近の通知を送信
        for skill in qs:
            days_left = (skill.expiry_date - date.today()).days
            Notification.send(
                user=skill.employee.user,
                type_=Notification.NotificationType.SKILL_EXPIRY,
                title=f'資格有効期限アラート：{skill.skill_name}',
                message=f'{skill.skill_name}の有効期限まであと{days_left}日です（{skill.expiry_date}）',
                related_url='/skills',
            )

        return Response(SkillSerializer(qs, many=True).data)
