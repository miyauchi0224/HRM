from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0005_alter_workrule_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='stamped_clock_in',
            field=models.TimeField(blank=True, null=True, verbose_name='出勤打刻時刻（原本）'),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='stamped_clock_out',
            field=models.TimeField(blank=True, null=True, verbose_name='退勤打刻時刻（原本）'),
        ),
    ]
