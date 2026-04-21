import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0001_initial'),
        ('employees', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # CourseAttachment
        migrations.CreateModel(
            name='CourseAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='learning/attachments/%Y/%m/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')),
                ('content_type', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('course', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='learning.learningcourse',
                )),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'verbose_name': 'コース添付ファイル', 'ordering': ['created_at']},
        ),
        # Quiz
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(default='理解度確認テスト', max_length=200)),
                ('description', models.TextField(blank=True)),
                ('pass_score', models.PositiveSmallIntegerField(default=70, verbose_name='合格点（%）')),
                ('time_limit_minutes', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='制限時間（分）')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='quiz',
                    to='learning.learningcourse',
                )),
            ],
            options={'verbose_name': '理解度テスト'},
        ),
        # QuizQuestion
        migrations.CreateModel(
            name='QuizQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('question_text', models.TextField(verbose_name='問題文')),
                ('question_type', models.CharField(
                    choices=[('choice', '選択式'), ('free_text', '自由記述')],
                    default='choice',
                    max_length=20,
                )),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('explanation', models.TextField(blank=True, verbose_name='解説（正解後に表示）')),
                ('points', models.PositiveSmallIntegerField(default=1, verbose_name='配点')),
                ('quiz', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='questions',
                    to='learning.quiz',
                )),
            ],
            options={'verbose_name': 'テスト問題', 'ordering': ['order']},
        ),
        # QuizChoice
        migrations.CreateModel(
            name='QuizChoice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('choice_text', models.CharField(max_length=500, verbose_name='選択肢テキスト')),
                ('is_correct', models.BooleanField(default=False, verbose_name='正解')),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='choices',
                    to='learning.quizquestion',
                )),
            ],
            options={'verbose_name': '選択肢', 'ordering': ['order']},
        ),
        # QuizAttempt
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('score', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='スコア（%）')),
                ('is_passed', models.BooleanField(blank=True, null=True)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='quiz_attempts',
                    to='employees.employee',
                )),
                ('quiz', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts',
                    to='learning.quiz',
                )),
            ],
            options={'verbose_name': 'テスト受験記録', 'ordering': ['-started_at']},
        ),
        # QuizAnswer
        migrations.CreateModel(
            name='QuizAnswer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('free_text_answer', models.TextField(blank=True, verbose_name='自由記述回答')),
                ('is_correct', models.BooleanField(blank=True, null=True, verbose_name='正解フラグ（自由記述はNull）')),
                ('attempt', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answers',
                    to='learning.quizattempt',
                )),
                ('question', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='answers',
                    to='learning.quizquestion',
                )),
                ('selected_choice', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='learning.quizchoice',
                    verbose_name='選択した選択肢',
                )),
            ],
            options={'verbose_name': 'テスト回答'},
        ),
        migrations.AddConstraint(
            model_name='quizanswer',
            constraint=models.UniqueConstraint(fields=['attempt', 'question'], name='unique_attempt_question'),
        ),
    ]
