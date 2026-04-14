import json
import boto3
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from .models import MBOGoal, MBOReport, DailyReport
from .serializers import MBOGoalSerializer, MBOReportSerializer, DailyReportSerializer
from apps.notifications.models import Notification


def _call_bedrock(prompt: str) -> str:
    """Amazon Bedrock (Claude) を呼び出してAI提案を取得"""
    try:
        client = boto3.client('bedrock-runtime', region_name=settings.AWS_REGION)
        body = json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}],
        })
        response = client.invoke_model(
            modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
            body=body,
        )
        result = json.loads(response['body'].read())
        return result['content'][0]['text']
    except Exception:
        return ''


class MBOGoalViewSet(viewsets.ModelViewSet):
    serializer_class   = MBOGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = MBOGoal.objects.prefetch_related('reports')
        year   = self.request.query_params.get('year')
        period = self.request.query_params.get('period')

        if user.is_manager:
            emp_id = self.request.query_params.get('employee_id')
            if emp_id:
                qs = qs.filter(employee_id=emp_id)
        else:
            qs = qs.filter(employee__user=user)

        if year:
            qs = qs.filter(year=year)
        if period:
            qs = qs.filter(period=period)
        return qs

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    def _total_weight(self, employee, year, period, exclude_id=None):
        """同一年度・期のウェイト合計を取得"""
        qs = MBOGoal.objects.filter(employee=employee, year=year, period=period)
        if exclude_id:
            qs = qs.exclude(id=exclude_id)
        return sum(g.weight for g in qs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d        = serializer.validated_data
        employee = request.user.employee
        total    = self._total_weight(employee, d['year'], d['period'])
        if total + d['weight'] > 100:
            return Response(
                {'error': f'ウェイト合計が100%を超えます（現在：{total}%）'},
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'], url_path='submit')
    def submit(self, request, pk=None):
        """目標を提出"""
        goal = self.get_object()
        if goal.employee.user != request.user:
            return Response({'error': '自分の目標のみ提出できます'}, status=status.HTTP_403_FORBIDDEN)
        goal.status = MBOGoal.Status.SUBMITTED
        goal.save()
        for manager in goal.employee.managers.all():
            Notification.send(
                user=manager.user,
                type_=Notification.NotificationType.MBO_FEEDBACK,
                title='MBO目標提出',
                message=f'{goal.employee.full_name}さんがMBO目標を提出しました',
                related_url='/mbo',
            )
        return Response(MBOGoalSerializer(goal).data)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """管理職が目標を承認 → 月報作成が可能になる"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        goal = self.get_object()
        if goal.status != MBOGoal.Status.SUBMITTED:
            return Response({'error': '提出済みの目標のみ承認できます'}, status=status.HTTP_400_BAD_REQUEST)
        goal.status = MBOGoal.Status.APPROVED
        goal.save()
        Notification.send(
            user=goal.employee.user,
            type_=Notification.NotificationType.MBO_FEEDBACK,
            title='MBO目標が承認されました',
            message=f'「{goal.title}」が承認されました。月間報告を作成できます。',
            related_url='/mbo',
        )
        return Response(MBOGoalSerializer(goal).data)

    @action(detail=True, methods=['patch'], url_path='evaluate')
    def evaluate(self, request, pk=None):
        """上司評価（スコア付与）"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        goal = self.get_object()
        score = request.data.get('manager_score')
        if score is None:
            return Response({'error': 'manager_score は必須です'}, status=status.HTTP_400_BAD_REQUEST)
        goal.manager_score = score
        goal.status        = MBOGoal.Status.EVALUATED
        goal.save()
        return Response(MBOGoalSerializer(goal).data)


class MBOReportViewSet(viewsets.ModelViewSet):
    serializer_class   = MBOReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user    = self.request.user
        goal_id = self.request.query_params.get('goal_id')
        qs      = MBOReport.objects.all()
        if goal_id:
            qs = qs.filter(goal_id=goal_id)
        if not user.is_manager:
            qs = qs.filter(goal__employee__user=user)
        return qs

    def perform_create(self, serializer):
        goal = serializer.validated_data.get('goal')
        if goal and goal.status not in (MBOGoal.Status.APPROVED, MBOGoal.Status.EVALUATED):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'goal': '承認済みの目標にのみ月間報告を作成できます'})
        serializer.save()

    @action(detail=True, methods=['patch'], url_path='submit')
    def submit(self, request, pk=None):
        """社員が月報を上司に申請"""
        report = self.get_object()
        if report.goal.employee.user != request.user:
            return Response({'error': '自分の月報のみ申請できます'}, status=status.HTTP_403_FORBIDDEN)
        if report.status != MBOReport.Status.DRAFT:
            return Response({'error': '下書きの月報のみ申請できます'}, status=status.HTTP_400_BAD_REQUEST)
        report.status = MBOReport.Status.SUBMITTED
        report.save()
        for manager in report.goal.employee.managers.all():
            Notification.send(
                user=manager.user,
                type_=Notification.NotificationType.MBO_FEEDBACK,
                title='MBO月報の申請が届きました',
                message=f'{report.goal.employee.full_name}さんから{report.month.strftime("%Y年%m月")}の月報申請があります',
                related_url='/mbo',
            )
        return Response(MBOReportSerializer(report).data)

    @action(detail=True, methods=['post'], url_path='ai-suggest')
    def ai_suggest(self, request, pk=None):
        """POST /api/v1/mbo/reports/{id}/ai-suggest/ - AI提案生成"""
        report = self.get_object()
        prompt = (
            f"あなたは人事評価の専門家です。以下のMBO月間報告を読んで、"
            f"改善点と具体的なアクション提案を日本語で300字以内で回答してください。\n\n"
            f"【行動内容】\n{report.action_content}\n\n"
            f"【結果・考察】\n{report.result}"
        )
        suggestion = _call_bedrock(prompt)
        report.ai_suggestion = suggestion
        report.save()
        return Response({'ai_suggestion': suggestion})

    @action(detail=True, methods=['patch'], url_path='comment')
    def comment(self, request, pk=None):
        """上司コメント登録"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        report = self.get_object()
        report.manager_comment = request.data.get('manager_comment', '')
        report.status          = MBOReport.Status.COMMENTED
        report.save()
        Notification.send(
            user=report.goal.employee.user,
            type_=Notification.NotificationType.MBO_FEEDBACK,
            title='MBO月間報告にコメントが届きました',
            message=f'{report.month.strftime("%Y年%m月")}の報告に上司からコメントがあります',
            related_url='/mbo',
        )
        return Response(MBOReportSerializer(report).data)


class DailyReportViewSet(viewsets.ModelViewSet):
    serializer_class   = DailyReportSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs   = DailyReport.objects.all()
        if not user.is_manager:
            qs = qs.filter(employee__user=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user.employee)

    @action(detail=True, methods=['post'], url_path='ai-suggest')
    def ai_suggest(self, request, pk=None):
        """日報へのAI提案"""
        report = self.get_object()
        prompt = (
            f"あなたはキャリアコーチです。以下の日報を読んで、"
            f"明日への改善点とポジティブなフィードバックを日本語で200字以内で回答してください。\n\n"
            f"{report.content}"
        )
        suggestion = _call_bedrock(prompt)
        report.ai_suggestion = suggestion
        report.save()
        return Response({'ai_suggestion': suggestion})
