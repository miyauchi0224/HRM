import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recruitment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # JobPosting
        migrations.AddField(
            model_name='jobposting',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='jobposting',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # Candidate
        migrations.AddField(
            model_name='candidate',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='candidate',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='candidate',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # Interview
        migrations.AddField(
            model_name='interview',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='interview',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='interview',
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
