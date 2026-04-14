import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TodoItem',
            fields=[
                ('id',          models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title',       models.CharField(max_length=200, verbose_name='タイトル')),
                ('description', models.TextField(blank=True, verbose_name='詳細')),
                ('status',      models.CharField(
                    choices=[('not_started', '未着手'), ('in_progress', '作業中'), ('done', '実施済み')],
                    default='not_started',
                    max_length=20,
                    verbose_name='ステータス',
                )),
                ('due_date',    models.DateField(blank=True, null=True, verbose_name='期限')),
                ('order',       models.PositiveIntegerField(default=0, verbose_name='表示順')),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('employee',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='todos',
                    to='employees.employee',
                )),
            ],
            options={
                'verbose_name': 'TODOアイテム',
                'ordering': ['status', 'order', '-created_at'],
            },
        ),
    ]
