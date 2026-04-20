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
            name='AssetCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='カテゴリ名')),
                ('description', models.TextField(blank=True)),
            ],
            options={'verbose_name': '資産カテゴリ'},
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('asset_number', models.CharField(max_length=50, unique=True, verbose_name='資産番号')),
                ('name', models.CharField(max_length=200, verbose_name='資産名')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets', to='assets.assetcategory')),
                ('serial_number', models.CharField(blank=True, max_length=100, verbose_name='シリアル番号')),
                ('model', models.CharField(blank=True, max_length=200, verbose_name='型番')),
                ('manufacturer', models.CharField(blank=True, max_length=100, verbose_name='メーカー')),
                ('purchase_date', models.DateField(blank=True, null=True, verbose_name='購入日')),
                ('purchase_price', models.PositiveIntegerField(blank=True, null=True, verbose_name='購入金額（円）')),
                ('warranty_expiry', models.DateField(blank=True, null=True, verbose_name='保証期限')),
                ('location', models.CharField(blank=True, max_length=200, verbose_name='保管場所')),
                ('status', models.CharField(choices=[('available', '利用可能'), ('in_use', '使用中'), ('maintenance', '修理中'), ('disposed', '廃棄済')], default='available', max_length=20)),
                ('condition', models.CharField(choices=[('new', '新品'), ('good', '良好'), ('fair', '普通'), ('poor', '劣化')], default='good', max_length=20)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_assets', to='employees.employee', verbose_name='使用者')),
                ('assigned_at', models.DateField(blank=True, null=True, verbose_name='貸出日')),
                ('note', models.TextField(blank=True, verbose_name='備考')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': '資産', 'ordering': ['asset_number']},
        ),
        migrations.CreateModel(
            name='AssetHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='assets.asset')),
                ('event_type', models.CharField(choices=[('assigned', '貸出'), ('returned', '返却'), ('maintenance', '修理'), ('disposed', '廃棄')], max_length=20)),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_history', to='employees.employee')),
                ('note', models.TextField(blank=True)),
                ('event_date', models.DateField(verbose_name='日付')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '資産履歴', 'ordering': ['-event_date']},
        ),
    ]
