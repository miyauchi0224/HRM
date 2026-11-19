from datetime import date

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsNotCustomer, IsHR
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.employees.models import Employee
from apps.notifications.models import Notification
from .models import PulseSurvey
from .serializers import PulseSurveySerializer
from .services import AnswerError, build_results, submit_answers


class PulseSurveyViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    """
    パルスサーベイ（詳細設計書 7.10）

    一覧・詳細・回答: 全社員（未公開は人事のみ）／作成・編集・公開・集計: 人事
    """
    serializer_class = PulseSurveySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'answer'):
            return [IsNotCustomer()]
        return [IsHR()]

    def get_queryset(self):
        qs = PulseSurvey.objects.prefetch_related('questions')
        if self.request.user.is_hr:
            return qs.all()
        return qs.filter(is_published=True)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        survey = self.get_object()
        if survey.is_published:
            return Response({'error': '公開済みです'}, status=status.HTTP_400_BAD_REQUEST)
        survey.is_published = True
        survey.save(update_fields=['is_published'])
        for emp in Employee.objects.select_related('user').filter(retire_date__isnull=True):
            if emp.user.is_customer:
                continue
            Notification.send(
                user=emp.user,
                type_=Notification.NotificationType.PULSE_SURVEY,
                title=f'【アンケート】{survey.title}',
                message=f'回答期間: {survey.start_date}〜{survey.end_date}'
                        f'（{"匿名" if survey.is_anonymous else "記名"}・数分で終わります）',
                related_url=f'/pulse/{survey.id}',
            )
        return Response(PulseSurveySerializer(survey, context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='answer')
    def answer(self, request, pk=None):
        survey   = self.get_object()
        employee = getattr(request.user, 'employee', None)
        if employee is None:
            return Response({'error': '社員情報が登録されていません'}, status=status.HTTP_404_NOT_FOUND)
        today = date.today()
        if not (survey.is_published and survey.start_date <= today <= survey.end_date):
            return Response({'error': '回答期間外です'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            submit_answers(survey, employee, request.data.get('answers', {}))
        except AnswerError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'submitted'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='results')
    def results(self, request, pk=None):
        return Response(build_results(self.get_object()))
