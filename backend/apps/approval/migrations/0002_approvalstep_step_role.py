from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalstep',
            name='step_role',
            field=models.CharField(
                choices=[('supervisor', '上司'), ('manager', '部門長'), ('accounting', '財務'), ('custom', 'カスタム')],
                default='custom',
                max_length=20,
                verbose_name='承認者の役割',
            ),
        ),
    ]
