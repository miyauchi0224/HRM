from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.AddField(model_name='employee', name='zip_code',
            field=models.CharField(blank=True, max_length=10, verbose_name='郵便番号')),
        migrations.AddField(model_name='employee', name='address',
            field=models.CharField(blank=True, max_length=200, verbose_name='住所')),
        migrations.AddField(model_name='employee', name='nearest_station',
            field=models.CharField(blank=True, max_length=100, verbose_name='最寄り駅')),
        migrations.AddField(model_name='employee', name='workplace_name',
            field=models.CharField(blank=True, max_length=200, verbose_name='勤務先名')),
        migrations.AddField(model_name='employee', name='workplace_address',
            field=models.CharField(blank=True, max_length=200, verbose_name='勤務先住所')),
        migrations.AddField(model_name='employee', name='workplace_phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='勤務先電話番号')),
        migrations.AddField(model_name='employee', name='commute_route',
            field=models.TextField(blank=True, verbose_name='通勤経路')),
    ]
