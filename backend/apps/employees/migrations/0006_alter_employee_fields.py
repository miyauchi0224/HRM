# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0005_softdelete_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='birth_date',
            field=models.DateField(blank=True, null=True, verbose_name='生年月日'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', '男性'), ('female', '女性'), ('other', 'その他')], max_length=10, null=True, verbose_name='性別'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='hire_date',
            field=models.DateField(blank=True, null=True, verbose_name='入社日'),
        ),
    ]
