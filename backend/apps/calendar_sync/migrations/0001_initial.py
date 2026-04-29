from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCalendarToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False, verbose_name='削除フラグ')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.CharField(blank=True, max_length=255, verbose_name='削除者')),
                ('provider', models.CharField(choices=[('ms', 'Microsoft'), ('google', 'Google')], max_length=20, verbose_name='プロバイダー')),
                ('access_token', models.TextField(verbose_name='アクセストークン')),
                ('refresh_token', models.TextField(blank=True, verbose_name='リフレッシュトークン')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='有効期限')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calendar_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'カレンダーOAuthトークン',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='usercalendartoken',
            unique_together={('user', 'provider')},
        ),
    ]
