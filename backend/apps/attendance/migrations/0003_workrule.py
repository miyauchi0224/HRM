from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_multi_project'),
    ]

    operations = [
        migrations.CreateModel(
            name='WorkRule',
            fields=[
                ('id',                 models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('name',               models.CharField(max_length=100, unique=True, verbose_name='ルール名')),
                ('work_start',         models.TimeField(verbose_name='定時開始')),
                ('work_end',           models.TimeField(verbose_name='定時終了')),
                ('standard_minutes',   models.PositiveIntegerField(default=480, verbose_name='所定労働時間（分）')),
                ('break_minutes',      models.PositiveIntegerField(default=60,  verbose_name='標準休憩時間（分）')),
                ('overtime_threshold', models.PositiveIntegerField(default=480, verbose_name='残業開始基準（分）')),
                ('is_default',         models.BooleanField(default=False, verbose_name='デフォルトルール')),
            ],
            options={'verbose_name': '勤怠ルール'},
        ),
    ]
