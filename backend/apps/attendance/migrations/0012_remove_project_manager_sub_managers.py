from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0011_projectmanager_model'),
    ]

    operations = [
        # manager FK を削除
        migrations.RemoveField(
            model_name='project',
            name='manager',
        ),
        # sub_managers M2M を削除
        migrations.RemoveField(
            model_name='project',
            name='sub_managers',
        ),
    ]
