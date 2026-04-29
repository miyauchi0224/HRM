import uuid
from django.db import models
from apps.employees.models import Employee
from apps.accounts.models import User
from apps.common.models import SoftDeleteModel


class DocumentCategory(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='カテゴリ名')
    slug = models.SlugField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'ドキュメントカテゴリ'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Document(SoftDeleteModel):
    class Visibility(models.TextChoices):
        ALL          = 'all',          '全社員'
        HR_ONLY      = 'hr_only',      '人事のみ'
        PERSONAL     = 'personal',     '個人'
        ROLE_MANAGER = 'role_manager', '管理職以上'
        PROJECT      = 'project',      'プロジェクトメンバー'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=300, verbose_name='タイトル')
    category = models.ForeignKey(
        DocumentCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents', verbose_name='カテゴリ'
    )
    target_employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, null=True, blank=True,
        related_name='personal_documents', verbose_name='対象社員'
    )
    target_project = models.ForeignKey(
        'attendance.Project', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='documents', verbose_name='対象プロジェクト'
    )
    visibility = models.CharField(
        max_length=20, choices=Visibility.choices, default=Visibility.ALL
    )
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='created_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'ドキュメント'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    @property
    def latest_file(self):
        return self.files.order_by('-version').first()


class DocumentFile(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='files')
    version = models.PositiveIntegerField(default=1, verbose_name='バージョン')
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name='ファイル')
    file_name = models.CharField(max_length=255, verbose_name='ファイル名')
    file_size = models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')
    content_type = models.CharField(max_length=100, verbose_name='MIMEタイプ')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ドキュメントファイル'
        ordering = ['-version']

    def __str__(self):
        return f'{self.document.title} v{self.version}'
