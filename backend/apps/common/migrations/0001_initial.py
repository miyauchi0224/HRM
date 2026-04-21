import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(
                    choices=[('create', '作成'), ('update', '更新'), ('delete', '削除（非表示）'), ('restore', '復元')],
                    max_length=20,
                    verbose_name='操作種別',
                )),
                ('app_label',   models.CharField(max_length=50, verbose_name='アプリ')),
                ('model_name',  models.CharField(max_length=100, verbose_name='モデル名')),
                ('object_id',   models.CharField(max_length=100, verbose_name='レコードID')),
                ('object_repr', models.CharField(blank=True, max_length=500, verbose_name='レコード概要')),
                ('changes',     models.JSONField(blank=True, default=dict, verbose_name='変更内容')),
                ('ip_address',  models.GenericIPAddressField(blank=True, null=True, verbose_name='IPアドレス')),
                ('timestamp',   models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='操作日時')),
                ('user', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='audit_logs',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='操作者',
                )),
            ],
            options={'verbose_name': '操作ログ', 'ordering': ['-timestamp']},
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['app_label', 'model_name', 'object_id'], name='auditlog_model_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'timestamp'], name='auditlog_user_ts_idx'),
        ),
    ]
