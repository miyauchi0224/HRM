from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expense', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='expenserequest',
            name='payment_type',
            field=models.CharField(
                choices=[('reimbursement', '立替払い'), ('advance', '先払い申請')],
                default='reimbursement',
                max_length=20,
                verbose_name='支払方法',
            ),
        ),
        migrations.AddField(
            model_name='expenserequest',
            name='rejected_reason',
            field=models.TextField(blank=True, verbose_name='却下理由'),
        ),
    ]
