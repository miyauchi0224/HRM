import uuid
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id',            models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title',         models.CharField(max_length=200, verbose_name='タイトル')),
                ('content',       models.TextField(verbose_name='本文（Markdown）')),
                ('category',      models.CharField(
                    choices=[
                        ('announcement', 'お知らせ'),
                        ('technical',    '技術情報'),
                        ('company_news', '社内報'),
                        ('department',   '部署連絡'),
                        ('other',        'その他'),
                    ],
                    default='announcement', max_length=20, verbose_name='カテゴリ',
                )),
                ('is_pinned',     models.BooleanField(default=False, verbose_name='ピン留め')),
                ('status',        models.CharField(
                    choices=[
                        ('draft',    '下書き'),
                        ('pending',  '承認待ち'),
                        ('approved', '公開中'),
                        ('rejected', '却下'),
                    ],
                    default='draft', max_length=20, verbose_name='ステータス',
                )),
                ('reject_reason', models.TextField(blank=True, verbose_name='却下理由')),
                ('published_at',  models.DateTimeField(blank=True, null=True, verbose_name='公開日時')),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
                ('author',        models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='intra_articles',
                    to='employees.employee',
                    verbose_name='投稿者',
                )),
                ('approver',      models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_articles',
                    to='employees.employee',
                    verbose_name='承認者',
                )),
            ],
            options={
                'verbose_name': '記事',
                'ordering': ['-is_pinned', '-published_at', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ArticleRead',
            fields=[
                ('id',      models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('read_at', models.DateTimeField(auto_now_add=True)),
                ('article', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reads',
                    to='intra.article',
                )),
                ('user',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='article_reads',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': '既読',
                'ordering': ['-read_at'],
                'unique_together': {('article', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ArticleComment',
            fields=[
                ('id',         models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content',    models.TextField(verbose_name='コメント本文')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('article',    models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='intra.article',
                )),
                ('author',     models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='intra_comments',
                    to='employees.employee',
                )),
            ],
            options={
                'verbose_name': '記事コメント',
                'ordering': ['created_at'],
            },
        ),
    ]
