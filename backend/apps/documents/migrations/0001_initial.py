import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0005_softdelete_fields'),
        ('accounts', '0004_user_openai_and_provider'),
        ('common', '0002_rename_auditlog_model_idx_common_audi_app_lab_0fa6cc_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentCategory',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='削除者',
                )),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='カテゴリ名')),
                ('slug', models.SlugField(max_length=50, unique=True)),
                ('order', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'ドキュメントカテゴリ',
                'ordering': ['order', 'name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='削除者',
                )),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=300, verbose_name='タイトル')),
                ('category', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='documents',
                    to='documents.documentcategory',
                    verbose_name='カテゴリ',
                )),
                ('target_employee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='personal_documents',
                    to='employees.employee',
                    verbose_name='対象社員',
                )),
                ('visibility', models.CharField(
                    choices=[
                        ('all', '全社員'),
                        ('hr_only', '人事のみ'),
                        ('personal', '個人'),
                    ],
                    default='all',
                    max_length=20,
                )),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_documents',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'ドキュメント',
                'ordering': ['-updated_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DocumentFile',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='削除者',
                )),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('document', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='files',
                    to='documents.document',
                )),
                ('version', models.PositiveIntegerField(default=1, verbose_name='バージョン')),
                ('file', models.FileField(upload_to='documents/%Y/%m/', verbose_name='ファイル')),
                ('file_name', models.CharField(max_length=255, verbose_name='ファイル名')),
                ('file_size', models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')),
                ('content_type', models.CharField(max_length=100, verbose_name='MIMEタイプ')),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='uploaded_documents',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'ドキュメントファイル',
                'ordering': ['-version'],
                'abstract': False,
            },
        ),
    ]
