import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('todo', '0001_initial'),
        ('attendance', '0002_multi_project'),
    ]

    operations = [
        # TodoItem にプロジェクト FK を追加
        migrations.AddField(
            model_name='todoitem',
            name='project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='todo_items',
                to='attendance.project',
                verbose_name='プロジェクト',
            ),
        ),
        # 日報モデルを作成
        migrations.CreateModel(
            name='DailyReport',
            fields=[
                ('id',          models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('report_date', models.DateField(verbose_name='報告日')),
                ('content',     models.TextField(verbose_name='本日の作業内容')),
                ('tomorrow',    models.TextField(blank=True, verbose_name='明日の予定')),
                ('issues',      models.TextField(blank=True, verbose_name='課題・連絡事項')),
                ('status',      models.CharField(
                    choices=[('draft', '下書き'), ('submitted', '提出済')],
                    default='draft', max_length=20,
                )),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('employee',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='todo_daily_reports',
                    to='employees.employee',
                    verbose_name='社員',
                )),
            ],
            options={
                'verbose_name': '日報',
                'ordering': ['-report_date'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='dailyreport',
            unique_together={('employee', 'report_date')},
        ),
    ]
