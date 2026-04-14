from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('intra', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='format',
            field=models.CharField(
                choices=[('text', 'テキスト'), ('markdown', 'Markdown'), ('html', 'HTML（リッチテキスト）')],
                default='markdown',
                max_length=10,
                verbose_name='記述形式',
            ),
        ),
    ]
