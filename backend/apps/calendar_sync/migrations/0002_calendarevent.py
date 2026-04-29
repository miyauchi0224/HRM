# Generated migration

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calendar_sync', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CalendarEvent',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='イベントタイトル')),
                ('start_datetime', models.DateTimeField(verbose_name='開始日時')),
                ('end_datetime', models.DateTimeField(verbose_name='終了日時')),
                ('provider', models.CharField(choices=[('ms', 'Microsoft'), ('google', 'Google'), ('local', 'ローカル')], default='local', max_length=20, verbose_name='プロバイダー')),
                ('external_id', models.CharField(blank=True, max_length=500, verbose_name='外部カレンダーID')),
                ('url', models.URLField(blank=True, verbose_name='イベントURL')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='削除者')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='calendar_events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'カレンダーイベント',
                'verbose_name_plural': 'カレンダーイベント',
                'ordering': ['-start_datetime'],
            },
        ),
        migrations.AddIndex(
            model_name='calendarevent',
            index=models.Index(fields=['user', 'start_datetime'], name='calendar_sy_user_id_start_d_idx'),
        ),
    ]
