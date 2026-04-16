import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        # 1. AttendanceRecord から project FK を削除
        migrations.RemoveField(
            model_name='attendancerecord',
            name='project',
        ),
        # 2. AttendanceProjectRecord テーブルを作成
        migrations.CreateModel(
            name='AttendanceProjectRecord',
            fields=[
                ('id',      models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)),
                ('minutes', models.PositiveIntegerField(verbose_name='作業時間（分）')),
                ('attendance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='project_records',
                    to='attendance.attendancerecord',
                    verbose_name='勤怠記録',
                )),
                ('project', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='attendance_records',
                    to='attendance.project',
                    verbose_name='プロジェクト',
                )),
            ],
            options={
                'verbose_name': 'プロジェクト作業記録',
                'ordering': ['project__code'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='attendanceprojectrecord',
            unique_together={('attendance', 'project')},
        ),
    ]
