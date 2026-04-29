from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0010_alter_project_manager'),
    ]

    operations = [
        # 1. ProjectManager テーブルを作成
        migrations.CreateModel(
            name='ProjectManager',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('primary', '主管理者'), ('secondary', '従管理者')], default='secondary', max_length=20, verbose_name='役割')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_deleted', models.BooleanField(default=False, verbose_name='削除フラグ')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='削除日時')),
                ('deleted_by', models.CharField(blank=True, max_length=255, verbose_name='削除者')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='managed_project_roles', to='employees.employee')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_managers', to='attendance.project')),
            ],
            options={
                'verbose_name': 'プロジェクト管理者',
                'ordering': ['role', 'created_at'],
            },
        ),

        # 2. 既存の manager FK から ProjectManager に移行（primary）
        migrations.RunPython(
            code=lambda apps, schema_editor: migrate_managers_to_m2m(apps),
            reverse_code=lambda apps, schema_editor: None,
        ),

        # 3. Unique constraint を追加
        migrations.AlterUniqueTogether(
            name='projectmanager',
            unique_together={('project', 'employee')},
        ),
    ]


def migrate_managers_to_m2m(apps):
    """既存の manager FK と sub_managers M2M を ProjectManager に移行"""
    Project = apps.get_model('attendance', 'Project')
    ProjectManager = apps.get_model('attendance', 'ProjectManager')

    for project in Project.objects.all():
        # 主管理者（manager FK）を ProjectManager に追加
        if project.manager:
            ProjectManager.objects.create(
                project=project,
                employee=project.manager,
                role='primary'
            )

        # 従管理者（sub_managers M2M）を ProjectManager に追加
        for employee in project.sub_managers.all():
            # 既に primary として登録されている場合はスキップ
            if not ProjectManager.objects.filter(project=project, employee=employee).exists():
                ProjectManager.objects.create(
                    project=project,
                    employee=employee,
                    role='secondary'
                )
