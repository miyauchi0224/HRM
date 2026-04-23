import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0005_softdelete_fields'),
        ('common', '0002_rename_auditlog_model_idx_common_audi_app_lab_0fa6cc_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardingTemplate',
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
                ('name', models.CharField(max_length=200, verbose_name='テンプレート名')),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='有効')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'オンボーディングテンプレート',
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OnboardingTemplateTask',
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
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tasks',
                    to='onboarding.onboardingtemplate',
                )),
                ('title', models.CharField(max_length=200, verbose_name='タスク名')),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(
                    choices=[
                        ('document', '書類提出'),
                        ('it', 'IT環境設定'),
                        ('training', '研修受講'),
                        ('facility', '施設案内'),
                        ('other', 'その他'),
                    ],
                    default='other',
                    max_length=20,
                )),
                ('due_days_from_hire', models.PositiveIntegerField(default=7, verbose_name='入社後N日以内')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='表示順')),
            ],
            options={
                'verbose_name': 'テンプレートタスク',
                'ordering': ['order', 'due_days_from_hire'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OnboardingAssignment',
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
                ('template', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignments',
                    to='onboarding.onboardingtemplate',
                )),
                ('employee', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='onboarding_assignments',
                    to='employees.employee',
                )),
                ('assigned_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_onboardings',
                    to='employees.employee',
                )),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'オンボーディングアサイン',
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='onboardingassignment',
            constraint=models.UniqueConstraint(
                fields=['template', 'employee'],
                name='unique_onboarding_assignment',
            ),
        ),
        migrations.CreateModel(
            name='OnboardingTaskItem',
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
                ('assignment', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_items',
                    to='onboarding.onboardingassignment',
                )),
                ('template_task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='task_items',
                    to='onboarding.onboardingtemplatetask',
                )),
                ('is_completed', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'タスク進捗',
                'abstract': False,
            },
        ),
        migrations.AddConstraint(
            model_name='onboardingtaskitem',
            constraint=models.UniqueConstraint(
                fields=['assignment', 'template_task'],
                name='unique_onboarding_task_item',
            ),
        ),
    ]
