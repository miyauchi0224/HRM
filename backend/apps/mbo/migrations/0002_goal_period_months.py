from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mbo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mbogoal',
            name='period_start_month',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='期間開始月（1-12）'),
        ),
        migrations.AddField(
            model_name='mbogoal',
            name='period_end_month',
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='期間終了月（1-12）'),
        ),
    ]
