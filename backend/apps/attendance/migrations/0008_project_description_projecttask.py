import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0007_softdelete_fields'),
        ('employees', '0005_softdelete_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='description',
            field=models.TextField(blank=True, verbose_name='概要'),
        ),
        migrations.CreateModel(
            name='ProjectTask',
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
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='attendance.project',
                    verbose_name='プロジェクト',
                )),
                ('title', models.CharField(max_length=200, verbose_name='タスク名')),
                ('description', models.TextField(blank=True, verbose_name='詳細')),
                ('assignee', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_tasks',
                    to='employees.employee',
                    verbose_name='担当者',
                )),
                ('status', models.CharField(
                    choices=[
                        ('todo', '未着手'),
                        ('in_progress', '進行中'),
                        ('review', 'レビュー中'),
                        ('done', '完了'),
                    ],
                    default='todo',
                    max_length=20,
                )),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='開始予定日')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='終了予定日')),
                ('progress', models.PositiveSmallIntegerField(default=0, verbose_name='進捗率(%)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='表示順')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'プロジェクトタスク',
                'ordering': ['order', 'start_date'],
                'abstract': False,
            },
        ),
    ]
