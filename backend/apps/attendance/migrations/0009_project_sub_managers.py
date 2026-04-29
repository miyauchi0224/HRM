from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0008_project_description_projecttask'),
        ('employees', '0005_softdelete_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='sub_managers',
            field=models.ManyToManyField(
                blank=True,
                related_name='sub_managed_projects',
                to='employees.employee',
                verbose_name='従管理者',
            ),
        ),
    ]
