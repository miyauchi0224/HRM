from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('skills', '0003_softdelete_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='skill',
            name='certificate_file',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='skills/certificates/%Y/%m/',
                verbose_name='認定証ファイル',
            ),
        ),
    ]
