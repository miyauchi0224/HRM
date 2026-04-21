import os
import uuid as _uuid
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Article, ArticleRead, ArticleComment
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer,
    ArticleWriteSerializer, ArticleReadSerializer, ArticleCommentSerializer,
)
from apps.notifications.models import Notification
from apps.accounts.models import User
from apps.common.mixins import SoftDeleteViewSetMixin


class ArticleViewSet(SoftDeleteViewSetMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'recent':
            return ArticleListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleWriteSerializer
        return ArticleDetailSerializer

    def get_queryset(self):
        user = self.request.user
        # 検索キーワード
        q = self.request.query_params.get('q', '')
        # カテゴリフィルタ
        category = self.request.query_params.get('category', '')

        # 公開済み記事 + 自分の記事（全ステータス）
        qs = Article.objects.select_related('author', 'approver').prefetch_related('reads', 'comments')

        if user.is_manager:
            # 管理職は全記事閲覧可能（下書き以外）
            qs = qs.filter(~Q(status='draft') | Q(author__user=user))
        else:
            # 社員は公開済み + 自分の記事
            qs = qs.filter(Q(status='approved') | Q(author__user=user))

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        if category:
            qs = qs.filter(category=category)

        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.employee)

    def retrieve(self, request, *args, **kwargs):
        """記事詳細取得 — 公開済みなら既読を自動登録"""
        instance = self.get_object()
        if instance.status == Article.Status.APPROVED:
            ArticleRead.objects.get_or_create(article=instance, user=request.user)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # ── アクション ──────────────────────────────────

    @action(detail=False, methods=['get'], url_path='recent')
    def recent(self, request):
        """ダッシュボード用：最新公開記事5件"""
        qs = Article.objects.filter(status=Article.Status.APPROVED) \
                            .select_related('author') \
                            .prefetch_related('reads') \
                            .order_by('-is_pinned', '-published_at')[:5]
        serializer = ArticleListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='submit')
    def submit(self, request, pk=None):
        """社員 → 承認申請"""
        article = self.get_object()
        if article.author.user != request.user:
            return Response({'error': '自分の記事のみ申請できます'}, status=status.HTTP_403_FORBIDDEN)
        if article.status not in (Article.Status.DRAFT, Article.Status.REJECTED):
            return Response({'error': '下書きまたは却下済みの記事のみ申請できます'}, status=status.HTTP_400_BAD_REQUEST)
        article.status = Article.Status.PENDING
        article.save()
        # 全管理職に通知
        for manager_user in User.objects.filter(role__in=['manager', 'hr', 'admin']):
            Notification.send(
                user=manager_user,
                type_=Notification.NotificationType.SYSTEM,
                title='イントラ記事の承認申請',
                message=f'{article.author.full_name}さんが記事「{article.title}」を申請しました',
                related_url=f'/intra/{article.id}',
            )
        return Response(ArticleDetailSerializer(article, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path='approve')
    def approve(self, request, pk=None):
        """管理職 → 承認・公開"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        article = self.get_object()
        if article.status != Article.Status.PENDING:
            return Response({'error': '承認待ちの記事のみ承認できます'}, status=status.HTTP_400_BAD_REQUEST)
        article.status      = Article.Status.APPROVED
        article.approver    = request.user.employee
        article.published_at = timezone.now()
        article.save()
        # 投稿者に通知
        Notification.send(
            user=article.author.user,
            type_=Notification.NotificationType.SYSTEM,
            title='記事が承認されました',
            message=f'「{article.title}」が承認・公開されました',
            related_url=f'/intra/{article.id}',
        )
        # 全社員に通知
        for emp_user in User.objects.filter(role='employee'):
            if emp_user != article.author.user:
                Notification.send(
                    user=emp_user,
                    type_=Notification.NotificationType.SYSTEM,
                    title='新しい記事が公開されました',
                    message=f'「{article.title}」が公開されました',
                    related_url=f'/intra/{article.id}',
                )
        return Response(ArticleDetailSerializer(article, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path='reject')
    def reject(self, request, pk=None):
        """管理職 → 却下（差し戻し）"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        article = self.get_object()
        if article.status != Article.Status.PENDING:
            return Response({'error': '承認待ちの記事のみ却下できます'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reject_reason', '')
        article.status        = Article.Status.REJECTED
        article.reject_reason = reason
        article.save()
        Notification.send(
            user=article.author.user,
            type_=Notification.NotificationType.SYSTEM,
            title='記事が却下されました',
            message=f'「{article.title}」が却下されました。理由: {reason}',
            related_url=f'/intra/{article.id}',
        )
        return Response(ArticleDetailSerializer(article, context={'request': request}).data)

    @action(detail=True, methods=['patch'], url_path='pin')
    def pin(self, request, pk=None):
        """管理職 → ピン留めトグル"""
        if not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        article = self.get_object()
        article.is_pinned = not article.is_pinned
        article.save()
        return Response({'is_pinned': article.is_pinned})

    @action(detail=True, methods=['get'], url_path='readers')
    def readers(self, request, pk=None):
        """既読者一覧（作者本人 or 管理職のみ閲覧可）"""
        article = self.get_object()
        if article.author.user != request.user and not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        reads = article.reads.select_related('user__employee').order_by('-read_at')
        serializer = ArticleReadSerializer(reads, many=True)
        total_employees = User.objects.filter(role__in=['employee', 'manager', 'hr']).count()
        return Response({
            'readers': serializer.data,
            'read_count': reads.count(),
            'total_employees': total_employees,
            'read_rate': round(reads.count() / total_employees * 100, 1) if total_employees else 0,
        })

    @action(detail=True, methods=['post'], url_path='comments')
    def add_comment(self, request, pk=None):
        """コメント投稿"""
        article = self.get_object()
        if article.status != Article.Status.APPROVED:
            return Response({'error': '公開済みの記事にのみコメントできます'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ArticleCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = ArticleComment.objects.create(
            article=article,
            author=request.user.employee,
            content=serializer.validated_data['content'],
        )
        # 記事投稿者に通知（自分のコメントは除く）
        if article.author.user != request.user:
            Notification.send(
                user=article.author.user,
                type_=Notification.NotificationType.SYSTEM,
                title='記事にコメントが届きました',
                message=f'{request.user.employee.full_name}さんが「{article.title}」にコメントしました',
                related_url=f'/intra/{article.id}',
            )
        return Response(ArticleCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'comments/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, pk=None, comment_id=None):
        """コメント削除（自分のコメントのみ）"""
        try:
            comment = ArticleComment.objects.get(id=comment_id, article_id=pk)
        except ArticleComment.DoesNotExist:
            return Response({'error: コメントが見つかりません'}, status=status.HTTP_404_NOT_FOUND)
        if comment.author.user != request.user and not request.user.is_manager:
            return Response({'error': '権限がありません'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 画像アップロード（スタンドアロンビュー） ────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_image(request):
    """
    POST /api/v1/intra/upload/
    エディタからの画像アップロード。
    レスポンス: { "url": "/media/intra/xxxx.jpg" }
    """
    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'imageファイルが必要です'}, status=status.HTTP_400_BAD_REQUEST)

    ext = os.path.splitext(image.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return Response({'error': f'許可されていない形式です（{ext}）'}, status=status.HTTP_400_BAD_REQUEST)

    if image.size > MAX_IMAGE_SIZE:
        return Response({'error': '10MB以下のファイルを選択してください'}, status=status.HTTP_400_BAD_REQUEST)

    # ユニークなファイル名で保存
    filename  = f'{_uuid.uuid4().hex}{ext}'
    save_dir  = os.path.join(settings.MEDIA_ROOT, 'intra')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    with open(save_path, 'wb') as f:
        for chunk in image.chunks():
            f.write(chunk)

    url = f'{settings.MEDIA_URL}intra/{filename}'
    return Response({'url': url}, status=status.HTTP_201_CREATED)
