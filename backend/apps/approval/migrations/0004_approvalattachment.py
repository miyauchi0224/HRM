import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0003_softdelete_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalAttachment',
            fields=[
                ('is_deleted', models.BooleanField(db_index=True, default=False, verbose_name='削除済み')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='削除者',
                )),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='approval/attachments/%Y/%m/')),
                ('file_name', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField()),
                ('content_type', models.CharField(max_length=100)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('request', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='file_attachments',
                    to='approval.approvalrequest',
                )),
                ('uploaded_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approval_file_uploads',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': '稟議添付ファイル',
                'ordering': ['uploaded_at'],
            },
        ),
    ]
