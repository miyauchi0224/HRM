import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_alter_messagereadstatus_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='chat/attachments/%Y/%m/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField(verbose_name='ファイルサイズ(bytes)')),
                ('content_type', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='chat.chatmessage',
                )),
            ],
            options={
                'verbose_name': '添付ファイル',
                'ordering': ['created_at'],
            },
        ),
    ]
