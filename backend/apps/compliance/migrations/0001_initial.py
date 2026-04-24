# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplianceChecklistSection',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=100, verbose_name='セクションタイトル')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='表示順')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='削除者')),
            ],
            options={
                'verbose_name': 'チェックリスト - セクション',
                'verbose_name_plural': 'チェックリスト - セクション',
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceChecklistItem',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='項目内容')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='表示順')),
                ('is_critical', models.BooleanField(default=False, verbose_name='重要項目フラグ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='削除者')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='compliance.compliancechecklistsection')),
            ],
            options={
                'verbose_name': 'チェックリスト - 項目',
                'verbose_name_plural': 'チェックリスト - 項目',
                'ordering': ['section', 'order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='ComplianceChecklistProgress',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_completed', models.BooleanField(default=False, verbose_name='完了フラグ')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完了日時')),
                ('notes', models.TextField(blank=True, verbose_name='備考')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='削除者')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_records', to='compliance.compliancechecklistitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compliance_progress', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'チェックリスト進捗',
                'verbose_name_plural': 'チェックリスト進捗',
                'ordering': ['item__section', 'item__order'],
                'unique_together': {('user', 'item')},
            },
        ),
    ]
