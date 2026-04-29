import csv
import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import HttpResponse
from apps.accounts.permissions import IsNotCustomer, IsHR
from apps.common.mixins import SoftDeleteViewSetMixin
from apps.notifications.models import Notification
from .models import StressCheckPeriod, StressCheckResponse, STRESS_CHECK_QUESTIONS
from .serializers import StressCheckPeriodSerializer, StressCheckResponseSerializer
from django.utils import timezone


class StressCheckPeriodViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    serializer_class = StressCheckPeriodSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        qs = StressCheckPeriod.objects.prefetch_related('responses').all()
        if not self.request.user.is_hr:
            return qs.filter(is_published=True)
        return qs

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy', 'publish',
                           'template_csv', 'import_questions'):
            return [IsHR()]
        return [IsNotCustomer()]

    @action(detail=False, methods=['get'], url_path='template-csv')
    def template_csv(self, request):
        """質問項目のCSVテンプレートをダウンロード"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['order', 'section', 'text', 'reverse'])
        for q in STRESS_CHECK_QUESTIONS:
            writer.writerow([q['order'], q['section'], q['text'], str(q['reverse']).lower()])
        content = '﻿' + output.getvalue()
        response = HttpResponse(content, content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="stress_check_template.csv"'
        return response

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        period = self.get_object()
        period.is_published = True
        period.save(update_fields=['is_published'])
        # 全社員に通知
        from apps.employees.models import Employee
        for emp in Employee.objects.select_related('user').all():
            Notification.send(
                user=emp.user,
                type_=Notification.NotificationType.STRESS_CHECK,
                title=f'【ストレスチェック】{period.title}',
                message=f'回答期間: {period.start_date}〜{period.end_date}。必ず回答してください。',
                related_url=f'/stress-check/{period.id}',
            )
        return Response({'status': 'published'})

    @action(detail=True, methods=['get'], url_path='group-analysis')
    def group_analysis(self, request, pk=None):
        if not request.user.is_hr:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        period = self.get_object()
        responses = period.responses.filter(is_submitted=True).select_related('employee')
        total = responses.count()
        high_stress = responses.filter(high_stress=True).count()
        avg_score = sum(r.total_score for r in responses) / total if total > 0 else 0
        # 部署別集計
        from collections import defaultdict
        dept_data = defaultdict(lambda: {'count': 0, 'high_stress': 0, 'total_score': 0})
        for r in responses:
            dept = r.employee.department
            dept_data[dept]['count'] += 1
            dept_data[dept]['total_score'] += r.total_score
            if r.high_stress:
                dept_data[dept]['high_stress'] += 1
        dept_summary = [
            {
                'department': dept,
                'count': data['count'],
                'high_stress_count': data['high_stress'],
                'avg_score': round(data['total_score'] / data['count'], 1) if data['count'] > 0 else 0,
            }
            for dept, data in dept_data.items()
        ]
        return Response({
            'period_id': str(period.id),
            'period_title': period.title,
            'total_responses': total,
            'high_stress_count': high_stress,
            'high_stress_rate': round(high_stress / total * 100, 1) if total > 0 else 0,
            'avg_score': round(avg_score, 1),
            'department_summary': dept_summary,
        })


class StressCheckResponseViewSet(viewsets.GenericViewSet):
    serializer_class = StressCheckResponseSerializer
    permission_classes = [IsNotCustomer]

    def get_queryset(self):
        user = self.request.user
        if user.is_hr:
            return StressCheckResponse.objects.select_related('employee', 'period').all()
        employee = getattr(user, 'employee', None)
        return StressCheckResponse.objects.filter(employee=employee).select_related('employee', 'period')

    def retrieve(self, request, pk=None):
        """GET /api/v1/stress-check/responses/{id}/"""
        instance = self.get_queryset().filter(id=pk).first()
        if not instance:
            return Response({'error': '回答が見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StressCheckResponseSerializer(instance).data)

    def list(self, request):
        """GET /api/v1/stress-check/responses/"""
        period_id = request.query_params.get('period_id')
        qs = self.get_queryset()
        if period_id:
            qs = qs.filter(period_id=period_id)
        return Response(StressCheckResponseSerializer(qs, many=True).data)

    @action(detail=False, methods=['post'], url_path='start')
    def start(self, request):
        """回答を開始（レコード作成またはリセット）"""
        period_id = request.data.get('period_id')
        employee = getattr(request.user, 'employee', None)
        if not employee:
            return Response({'error': '社員情報がありません'}, status=status.HTTP_404_NOT_FOUND)
        period = StressCheckPeriod.objects.filter(id=period_id, is_published=True).first()
        if not period:
            return Response({'error': '実施期間が見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        response, _ = StressCheckResponse.objects.get_or_create(
            period=period,
            employee=employee,
            defaults={'answers': {}},
        )
        return Response(StressCheckResponseSerializer(response).data)

    @action(detail=True, methods=['patch'], url_path='save')
    def save_answers(self, request, pk=None):
        """途中保存"""
        instance = self.get_queryset().filter(id=pk, is_submitted=False).first()
        if not instance:
            return Response({'error': '回答が見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        answers = request.data.get('answers', {})
        instance.answers = answers
        instance.save(update_fields=['answers'])
        return Response(StressCheckResponseSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """最終提出・スコア計算"""
        instance = self.get_queryset().filter(id=pk, is_submitted=False).first()
        if not instance:
            return Response({'error': '回答が見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        answers = request.data.get('answers', instance.answers)
        instance.answers = answers
        instance.calculate_score()
        instance.is_submitted = True
        instance.submitted_at = timezone.now()
        instance.save()
        return Response(StressCheckResponseSerializer(instance).data)
