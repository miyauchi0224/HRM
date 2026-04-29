# Generated migration

from django.db import migrations, models


def migrate_role_to_roles(apps, schema_editor):
    """既存の role フィールドの値を roles リストに移行"""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        if not user.roles:
            user.roles = [user.role] if user.role else []
            user.save(update_fields=['roles'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_user_openai_and_provider'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.JSONField(blank=True, default=list, verbose_name='ロール（複数）'),
        ),
        migrations.RunPython(migrate_role_to_roles, migrations.RunPython.noop),
    ]
