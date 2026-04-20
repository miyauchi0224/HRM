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
            name='LearningCourse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='コースタイトル')),
                ('description', models.TextField(verbose_name='コース説明')),
                ('course_type', models.CharField(choices=[('elearning', 'eラーニング'), ('classroom', '集合研修'), ('ojt', 'OJT'), ('external', '外部研修')], max_length=20)),
                ('thumbnail_url', models.URLField(blank=True)),
                ('duration_minutes', models.PositiveIntegerField(default=0, verbose_name='所要時間（分）')),
                ('is_required', models.BooleanField(default=False, verbose_name='必須研修')),
                ('status', models.CharField(choices=[('draft', '下書き'), ('published', '公開中'), ('archived', 'アーカイブ')], default='draft', max_length=20)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('target_roles', models.JSONField(blank=True, default=list, verbose_name='対象ロール')),
                ('tags', models.JSONField(blank=True, default=list, verbose_name='タグ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'コース', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='CourseContent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='contents', to='learning.learningcourse')),
                ('title', models.CharField(max_length=200)),
                ('content_type', models.CharField(choices=[('text', 'テキスト'), ('video', '動画'), ('slide', 'スライド'), ('quiz', 'クイズ')], max_length=20)),
                ('body', models.TextField(blank=True, verbose_name='テキストコンテンツ')),
                ('url', models.URLField(blank=True, verbose_name='動画・スライドURL')),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'verbose_name': 'コンテンツ', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='learning.learningcourse')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='employees.employee')),
                ('status', models.CharField(choices=[('not_started', '未受講'), ('in_progress', '受講中'), ('completed', '修了')], default='not_started', max_length=20)),
                ('progress_pct', models.PositiveSmallIntegerField(default=0, verbose_name='進捗率（%）')),
                ('score', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='テストスコア')),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True, verbose_name='期限日')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '受講記録', 'ordering': ['-created_at'], 'unique_together': {('course', 'employee')}},
        ),
    ]
