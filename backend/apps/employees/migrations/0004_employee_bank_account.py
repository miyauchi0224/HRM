from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_employee_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='bank_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='銀行名'),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_branch',
            field=models.CharField(blank=True, max_length=100, verbose_name='支店名'),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_account_type',
            field=models.CharField(blank=True, help_text='普通 / 当座', max_length=20, verbose_name='口座種別'),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_account_number',
            field=models.CharField(blank=True, max_length=20, verbose_name='口座番号'),
        ),
        migrations.AddField(
            model_name='employee',
            name='bank_account_holder',
            field=models.CharField(blank=True, max_length=100, verbose_name='口座名義'),
        ),
    ]
