import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0006_attendancerecord_stamped_times'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Project
        migrations.AddField(
            model_name='project',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='project',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='project',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # WorkRule
        migrations.AddField(
            model_name='workrule',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='workrule',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='workrule',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # AttendanceRecord
        migrations.AddField(
            model_name='attendancerecord',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # AttendanceProjectRecord
        migrations.AddField(
            model_name='attendanceprojectrecord',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='attendanceprojectrecord',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='attendanceprojectrecord',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # AttendanceModRequest
        migrations.AddField(
            model_name='attendancemodrequest',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='attendancemodrequest',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='attendancemodrequest',
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
