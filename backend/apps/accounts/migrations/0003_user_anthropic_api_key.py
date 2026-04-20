from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='anthropic_api_key',
            field=models.CharField(blank=True, max_length=200, verbose_name='Anthropic APIキー'),
        ),
    ]
