import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
        ('attendance', '0007_softdelete_fields'),
    ]

    operations = [
        # visibility フィールドの choices を拡張（max_length も 20 のまま OK）
        migrations.AlterField(
            model_name='document',
            name='visibility',
            field=models.CharField(
                choices=[
                    ('all',          '全社員'),
                    ('hr_only',      '人事のみ'),
                    ('personal',     '個人'),
                    ('role_manager', '管理職以上'),
                    ('project',      'プロジェクトメンバー'),
                ],
                default='all',
                max_length=20,
            ),
        ),
        # target_project FK を追加
        migrations.AddField(
            model_name='document',
            name='target_project',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documents',
                to='attendance.project',
                verbose_name='対象プロジェクト',
            ),
        ),
    ]
