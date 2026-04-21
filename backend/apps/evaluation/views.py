from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsHR, IsNotCustomer

from .models import EvaluationPeriod, EvaluationQuestion, Evaluation360, EvaluationScore
from .serializers import (EvaluationPeriodSerializer, EvaluationQuestionSerializer,
                          Evaluation360Serializer)
from apps.common.mixins import SoftDeleteViewSetMixin


class EvaluationPeriodViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = EvaluationPeriod.objects.all()
    serializer_class = EvaluationPeriodSerializer
    permission_classes = [IsHR]


class EvaluationQuestionViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    queryset = EvaluationQuestion.objects.filter(is_active=True)
    serializer_class = EvaluationQuestionSerializer
    permission_classes = [IsHR]


class Evaluation360ViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = Evaluation360Serializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        qs = Evaluation360.objects.select_related('period', 'subject', 'evaluator').prefetch_related('scores')
        if user.is_manager:
            return qs.all()
        try:
            emp = user.employee
            return qs.filter(evaluator=emp) | qs.filter(subject=emp)
        except Exception:
            return qs.none()

    def perform_create(self, serializer):
        serializer.save(evaluator=self.request.user.employee)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        obj = self.get_object()
        if obj.evaluator.user != request.user:
            return Response({'error': '自分の評価のみ提出できます'}, status=status.HTTP_403_FORBIDDEN)
        obj.is_submitted = True
        obj.submitted_at = timezone.now()
        obj.save()
        return Response(Evaluation360Serializer(obj).data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """評価対象者ごとの平均スコアサマリー"""
        period_id = request.query_params.get('period')
        subject_id = request.query_params.get('subject')
        qs = Evaluation360.objects.filter(is_submitted=True)
        if period_id:
            qs = qs.filter(period_id=period_id)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)

        result = {}
        for ev in qs.prefetch_related('scores__question'):
            for score in ev.scores.all():
                key = str(score.question_id)
                if key not in result:
                    result[key] = {'question': score.question.text, 'scores': []}
                result[key]['scores'].append(score.score)

        summary = []
        for key, data in result.items():
            avg = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
            summary.append({'question_id': key, 'question': data['question'],
                            'avg_score': round(avg, 2), 'count': len(data['scores'])})
        return Response(summary)
