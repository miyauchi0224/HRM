from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_anthropic_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='openai_api_key',
            field=models.CharField(blank=True, max_length=200, verbose_name='OpenAI APIキー'),
        ),
        migrations.AddField(
            model_name='user',
            name='ai_provider',
            field=models.CharField(
                choices=[('anthropic', 'Anthropic (Claude)'), ('openai', 'OpenAI (ChatGPT)')],
                default='anthropic',
                max_length=20,
                verbose_name='使用するAIプロバイダー',
            ),
        ),
    ]
