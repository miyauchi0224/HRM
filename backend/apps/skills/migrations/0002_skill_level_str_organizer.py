from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skill',
            name='level',
            field=models.CharField(blank=True, max_length=50, verbose_name='レベル'),
        ),
        migrations.AddField(
            model_name='skill',
            name='organizer',
            field=models.CharField(blank=True, max_length=100, verbose_name='主催者・発行機関'),
        ),
    ]
