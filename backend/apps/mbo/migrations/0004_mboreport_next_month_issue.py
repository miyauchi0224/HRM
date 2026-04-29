from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mbo', '0003_softdelete_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='mboreport',
            name='next_month_issue',
            field=models.TextField(blank=True, verbose_name='次月の課題'),
        ),
    ]
