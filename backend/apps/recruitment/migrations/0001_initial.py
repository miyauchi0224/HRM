import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('employees', '0004_employee_bank_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobPosting',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='求人タイトル')),
                ('department', models.CharField(blank=True, max_length=100, verbose_name='部署')),
                ('employment_type', models.CharField(choices=[('full_time', '正社員'), ('part_time', 'パートタイム'), ('contract', '契約社員'), ('intern', 'インターン')], max_length=20)),
                ('description', models.TextField(verbose_name='仕事内容')),
                ('requirements', models.TextField(verbose_name='応募要件')),
                ('preferred', models.TextField(blank=True, verbose_name='歓迎要件')),
                ('salary_range', models.CharField(blank=True, max_length=100, verbose_name='給与レンジ')),
                ('location', models.CharField(blank=True, max_length=200, verbose_name='勤務地')),
                ('status', models.CharField(choices=[('draft', '下書き'), ('open', '募集中'), ('closed', '募集終了')], default='draft', max_length=20)),
                ('open_date', models.DateField(blank=True, null=True)),
                ('close_date', models.DateField(blank=True, null=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '求人票', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('job_posting', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='recruitment.jobposting', verbose_name='応募求人')),
                ('full_name', models.CharField(max_length=100, verbose_name='氏名')),
                ('email', models.EmailField(verbose_name='メールアドレス')),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('resume_url', models.URLField(blank=True, verbose_name='履歴書URL')),
                ('portfolio_url', models.URLField(blank=True, verbose_name='ポートフォリオURL')),
                ('source', models.CharField(blank=True, max_length=100, verbose_name='応募経路')),
                ('status', models.CharField(choices=[('new', '新規'), ('screening', '書類選考'), ('interview1', '一次面接'), ('interview2', '二次面接'), ('final', '最終面接'), ('offer', '内定'), ('hired', '入社'), ('rejected', '不採用'), ('withdrawn', '辞退')], default='new', max_length=20)),
                ('note', models.TextField(blank=True, verbose_name='メモ')),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_candidates', to='employees.employee', verbose_name='担当者')),
                ('applied_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': '応募者', 'ordering': ['-applied_at']},
        ),
        migrations.CreateModel(
            name='Interview',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('candidate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interviews', to='recruitment.candidate')),
                ('interviewer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interviews_conducted', to='employees.employee', verbose_name='面接官')),
                ('scheduled_at', models.DateTimeField(verbose_name='面接日時')),
                ('location', models.CharField(blank=True, max_length=200, verbose_name='場所/URL')),
                ('result', models.CharField(blank=True, max_length=20, verbose_name='結果（pass/fail/tbd）')),
                ('feedback', models.TextField(blank=True, verbose_name='フィードバック')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '面接', 'ordering': ['scheduled_at']},
        ),
    ]
