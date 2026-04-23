import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0005_softdelete_fields'),
        ('common', '0002_rename_auditlog_model_idx_common_audi_app_lab_0fa6cc_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StressCheckPeriod',
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
                ('title', models.CharField(max_length=200, verbose_name='実施タイトル')),
                ('start_date', models.DateField(verbose_name='回答開始日')),
                ('end_date', models.DateField(verbose_name='回答終了日')),
                ('is_published', models.BooleanField(default=False, verbose_name='公開済み')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'ストレスチェック実施期間',
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StressCheckResponse',
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
                ('period', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='stress_check.stresscheckperiod',
                )),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='stress_check_responses',
                    to='employees.employee',
                )),
                ('answers', models.JSONField(default=dict, verbose_name='回答（問番号→スコア1-4）')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('is_submitted', models.BooleanField(default=False)),
                ('high_stress', models.BooleanField(default=False, verbose_name='高ストレス')),
                ('total_score', models.IntegerField(default=0, verbose_name='合計スコア')),
            ],
            options={
                'verbose_name': 'ストレスチェック回答',
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='stresscheckresponse',
            constraint=models.UniqueConstraint(
                fields=['period', 'employee'],
                name='unique_stress_check_response',
            ),
        ),
    ]
