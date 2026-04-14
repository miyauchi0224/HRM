import uuid
from django.db import models
from django.utils import timezone
from apps.employees.models import Employee
from apps.accounts.models import User


class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT    = 'draft',    '下書き'
        PENDING  = 'pending',  '承認待ち'
        APPROVED = 'approved', '公開中'
        REJECTED = 'rejected', '却下'

    class Category(models.TextChoices):
        ANNOUNCEMENT = 'announcement', 'お知らせ'
        TECHNICAL    = 'technical',    '技術情報'
        COMPANY_NEWS = 'company_news', '社内報'
        DEPARTMENT   = 'department',   '部署連絡'
        OTHER        = 'other',        'その他'

    class Format(models.TextChoices):
        TEXT     = 'text',     'テキスト'
        MARKDOWN = 'markdown', 'Markdown'
        HTML     = 'html',     'HTML（リッチテキスト）'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author       = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name='intra_articles', verbose_name='投稿者'
    )
    approver     = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_articles', verbose_name='承認者'
    )
    title        = models.CharField(max_length=200, verbose_name='タイトル')
    content      = models.TextField(verbose_name='本文')
    format       = models.CharField(
        max_length=10, choices=Format.choices, default=Format.MARKDOWN, verbose_name='記述形式'
    )
    category     = models.CharField(
        max_length=20, choices=Category.choices, default=Category.ANNOUNCEMENT, verbose_name='カテゴリ'
    )
    is_pinned    = models.BooleanField(default=False, verbose_name='ピン留め')
    status       = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT, verbose_name='ステータス'
    )
    reject_reason = models.TextField(blank=True, verbose_name='却下理由')
    published_at  = models.DateTimeField(null=True, blank=True, verbose_name='公開日時')
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '記事'
        ordering     = ['-is_pinned', '-published_at', '-created_at']

    def __str__(self):
        return self.title

    @property
    def read_count(self):
        return self.reads.count()

    @property
    def comment_count(self):
        return self.comments.count()


class ArticleRead(models.Model):
    """既読管理 — 同一ユーザーは1レコードのみ"""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article    = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reads')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='article_reads')
    read_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('article', 'user')
        verbose_name    = '既読'
        ordering        = ['-read_at']


class ArticleComment(models.Model):
    """記事コメント"""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article    = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='intra_comments')
    content    = models.TextField(verbose_name='コメント本文')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '記事コメント'
        ordering     = ['created_at']

    def __str__(self):
        return f'{self.author} → {self.article.title[:30]}'
