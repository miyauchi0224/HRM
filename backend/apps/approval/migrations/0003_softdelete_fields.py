import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('approval', '0002_approvalstep_step_role'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ApprovalTemplate
        migrations.AddField(
            model_name='approvaltemplate',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='approvaltemplate',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='approvaltemplate',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # ApprovalRequest
        migrations.AddField(
            model_name='approvalrequest',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='approvalrequest',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='approvalrequest',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
        # ApprovalStep
        migrations.AddField(
            model_name='approvalstep',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False, verbose_name='削除済み'),
        ),
        migrations.AddField(
            model_name='approvalstep',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='削除日時'),
        ),
        migrations.AddField(
            model_name='approvalstep',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
                verbose_name='削除者',
            ),
        ),
    ]
