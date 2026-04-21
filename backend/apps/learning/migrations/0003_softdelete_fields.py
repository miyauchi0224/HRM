import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0002_courseattachment_quiz_quizquestion_quizchoice_quizattempt_quizanswer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # LearningCourse
        migrations.AddField(
            model_name='learningcourse',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='learningcourse',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='learningcourse',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # CourseContent
        migrations.AddField(
            model_name='coursecontent',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='coursecontent',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='coursecontent',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # CourseAttachment
        migrations.AddField(
            model_name='courseattachment',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='courseattachment',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # CourseEnrollment
        migrations.AddField(
            model_name='courseenrollment',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # Quiz
        migrations.AddField(
            model_name='quiz',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='quiz',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # QuizQuestion
        migrations.AddField(
            model_name='quizquestion',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='quizquestion',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # QuizChoice
        migrations.AddField(
            model_name='quizchoice',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='quizchoice',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='quizchoice',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # QuizAttempt
        migrations.AddField(
            model_name='quizattempt',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='quizattempt',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # QuizAnswer
        migrations.AddField(
            model_name='quizanswer',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='quizanswer',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='quizanswer',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
    ]
