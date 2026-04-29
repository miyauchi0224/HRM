from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mbo', '0004_mboreport_next_month_issue'),
    ]

    operations = [
        migrations.AddField(
            model_name='mboreport',
            name='self_score',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True, verbose_name='自己評価'),
        ),
    ]
