import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0004_employee_bank_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApprovalTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='テンプレート名')),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '稟議テンプレート', 'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='件名')),
                ('category', models.CharField(choices=[('purchase', '購買申請'), ('travel', '出張申請'), ('contract', '契約申請'), ('budget', '予算申請'), ('hr', '人事申請'), ('other', 'その他')], max_length=20, verbose_name='カテゴリ')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='employees.employee', verbose_name='申請者')),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requests', to='approval.approvaltemplate')),
                ('amount', models.PositiveIntegerField(blank=True, null=True, verbose_name='金額（円）')),
                ('content', models.TextField(verbose_name='申請内容')),
                ('attachments', models.JSONField(blank=True, default=list, verbose_name='添付ファイルURL一覧')),
                ('status', models.CharField(choices=[('draft', '下書き'), ('pending', '審査中'), ('approved', '承認済'), ('rejected', '却下'), ('withdrawn', '取り下げ')], default='draft', max_length=20, verbose_name='ステータス')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': '稟議申請', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ApprovalStep',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='approval.approvalrequest')),
                ('approver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_steps', to='employees.employee', verbose_name='承認者')),
                ('order', models.PositiveSmallIntegerField(verbose_name='承認順序')),
                ('decision', models.CharField(choices=[('pending', '未決'), ('approved', '承認'), ('rejected', '却下'), ('skipped', 'スキップ')], default='pending', max_length=20)),
                ('comment', models.TextField(blank=True, verbose_name='コメント')),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={'verbose_name': '承認ステップ', 'ordering': ['order'], 'unique_together': {('request', 'order')}},
        ),
    ]
