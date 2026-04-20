import uuid
from django.db import models
from apps.employees.models import Employee


class AssetCategory(models.Model):
    """資産カテゴリ"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name='カテゴリ名')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = '資産カテゴリ'

    def __str__(self):
        return self.name


class Asset(models.Model):
    """社内資産（PC・スマホ・備品等）"""

    class Status(models.TextChoices):
        AVAILABLE = 'available', '利用可能'
        IN_USE = 'in_use', '使用中'
        MAINTENANCE = 'maintenance', '修理中'
        DISPOSED = 'disposed', '廃棄済'

    class Condition(models.TextChoices):
        NEW = 'new', '新品'
        GOOD = 'good', '良好'
        FAIR = 'fair', '普通'
        POOR = 'poor', '劣化'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_number = models.CharField(max_length=50, unique=True, verbose_name='資産番号')
    name = models.CharField(max_length=200, verbose_name='資産名')
    category = models.ForeignKey(AssetCategory, on_delete=models.SET_NULL, null=True,
                                 related_name='assets')
    serial_number = models.CharField(max_length=100, blank=True, verbose_name='シリアル番号')
    model = models.CharField(max_length=200, blank=True, verbose_name='型番')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='メーカー')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='購入日')
    purchase_price = models.PositiveIntegerField(null=True, blank=True, verbose_name='購入金額（円）')
    warranty_expiry = models.DateField(null=True, blank=True, verbose_name='保証期限')
    location = models.CharField(max_length=200, blank=True, verbose_name='保管場所')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GOOD)
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_assets', verbose_name='使用者')
    assigned_at = models.DateField(null=True, blank=True, verbose_name='貸出日')
    note = models.TextField(blank=True, verbose_name='備考')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = '資産'
        ordering = ['asset_number']

    def __str__(self):
        return f'{self.asset_number} {self.name}'


class AssetHistory(models.Model):
    """資産の貸出・返却・修理履歴"""

    class EventType(models.TextChoices):
        ASSIGNED = 'assigned', '貸出'
        RETURNED = 'returned', '返却'
        MAINTENANCE = 'maintenance', '修理'
        DISPOSED = 'disposed', '廃棄'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='history')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='asset_history')
    note = models.TextField(blank=True)
    event_date = models.DateField(verbose_name='日付')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '資産履歴'
        ordering = ['-event_date']
