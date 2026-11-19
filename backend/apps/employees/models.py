import uuid
from django.db import models
from apps.accounts.models import User
from apps.common.models import SoftDeleteModel


class Employee(SoftDeleteModel):
    class Gender(models.TextChoices):
        MALE   = 'male',   '男性'
        FEMALE = 'female', '女性'
        OTHER  = 'other',  'その他'

    class EmploymentType(models.TextChoices):
        FULL_TIME  = 'full_time',  '正社員'
        PART_TIME  = 'part_time',  'パート'
        CONTRACT   = 'contract',   '契約社員'
        DISPATCH   = 'dispatch',   '派遣社員'

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    employee_number   = models.CharField(max_length=20, unique=True, verbose_name='社員番号')
    last_name         = models.CharField(max_length=50, verbose_name='姓')
    first_name        = models.CharField(max_length=50, blank=True, verbose_name='名')
    last_name_kana    = models.CharField(max_length=50, blank=True, verbose_name='姓（カナ）')
    first_name_kana   = models.CharField(max_length=50, blank=True, verbose_name='名（カナ）')
    birth_date        = models.DateField(null=True, blank=True, verbose_name='生年月日')
    gender            = models.CharField(max_length=10, choices=Gender.choices, null=True, blank=True, verbose_name='性別')
    hire_date         = models.DateField(null=True, blank=True, verbose_name='入社日')
    retire_date       = models.DateField(null=True, blank=True, verbose_name='退職日')
    department        = models.CharField(max_length=100, verbose_name='部署')
    position          = models.CharField(max_length=100, verbose_name='役職')
    grade             = models.PositiveIntegerField(default=1, verbose_name='等級')
    employment_type   = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    phone             = models.CharField(max_length=20, blank=True, verbose_name='電話番号')
    personal_email    = models.EmailField(blank=True, verbose_name='個人メール')
    # 住所
    zip_code          = models.CharField(max_length=10, blank=True, verbose_name='郵便番号')
    address           = models.CharField(max_length=200, blank=True, verbose_name='住所')
    nearest_station   = models.CharField(max_length=100, blank=True, verbose_name='最寄り駅')
    # 勤務先
    workplace_name    = models.CharField(max_length=200, blank=True, verbose_name='勤務先名')
    workplace_address = models.CharField(max_length=200, blank=True, verbose_name='勤務先住所')
    workplace_phone   = models.CharField(max_length=20, blank=True, verbose_name='勤務先電話番号')
    # 通勤経路
    commute_route     = models.TextField(blank=True, verbose_name='通勤経路')
    avatar            = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='アバター画像')
    # 銀行口座情報（給与振込先）
    bank_name         = models.CharField(max_length=100, blank=True, verbose_name='銀行名')
    bank_branch       = models.CharField(max_length=100, blank=True, verbose_name='支店名')
    bank_account_type = models.CharField(max_length=20, blank=True, verbose_name='口座種別',
                                         help_text='普通 / 当座')
    bank_account_number = models.CharField(max_length=20, blank=True, verbose_name='口座番号')
    bank_account_holder = models.CharField(max_length=100, blank=True, verbose_name='口座名義')
    managers          = models.ManyToManyField('self', symmetrical=False, blank=True,
                                               related_name='subordinates', verbose_name='上司')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = '社員情報'
        verbose_name_plural = '社員情報'
        ordering            = ['employee_number']

    def __str__(self):
        return f'{self.last_name} {self.first_name}（{self.employee_number}）'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name}'


class EmergencyContact(SoftDeleteModel):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='emergency_contacts')
    name         = models.CharField(max_length=100, verbose_name='氏名')
    relationship = models.CharField(max_length=50, verbose_name='続柄')
    phone        = models.CharField(max_length=20, verbose_name='電話番号')
    sort_order   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class FamilyMember(SoftDeleteModel):
    class Relationship(models.TextChoices):
        SPOUSE   = 'spouse',   '配偶者'
        CHILD    = 'child',    '子'
        PARENT   = 'parent',   '親'
        SIBLING  = 'sibling',  '兄弟姉妹'
        OTHER    = 'other',    'その他'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='family_members')
    name         = models.CharField(max_length=100, verbose_name='氏名')
    relationship = models.CharField(max_length=20, choices=Relationship.choices, verbose_name='続柄')
    birth_date   = models.DateField(verbose_name='生年月日')
    is_dependent = models.BooleanField(default=False, verbose_name='扶養家族')

    class Meta:
        verbose_name = '家族構成'


class EmploymentHistory(SoftDeleteModel):
    """
    異動・昇格履歴（詳細設計書 7.5）

    - 社員情報の部署・役職・等級・雇用形態が変わると自動で記録される（is_applied=True）
    - 人事が未来日の発令を登録すると is_applied=False で予約され、発令日に反映される
    """
    class ChangeType(models.TextChoices):
        TRANSFER        = 'transfer',               '異動'
        PROMOTION       = 'promotion',              '昇格'
        DEMOTION        = 'demotion',               '降格'
        POSITION_CHANGE = 'position_change',        '役職変更'
        EMPLOYMENT_TYPE = 'employment_type_change', '雇用形態変更'
        OTHER           = 'other',                  'その他'

    id                     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee               = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='employment_histories')
    effective_date         = models.DateField(verbose_name='発令日')
    change_type            = models.CharField(max_length=30, choices=ChangeType.choices, verbose_name='種別')
    department_before      = models.CharField(max_length=100, blank=True)
    department_after       = models.CharField(max_length=100, blank=True)
    position_before        = models.CharField(max_length=100, blank=True)
    position_after         = models.CharField(max_length=100, blank=True)
    grade_before           = models.PositiveIntegerField(null=True, blank=True)
    grade_after            = models.PositiveIntegerField(null=True, blank=True)
    employment_type_before = models.CharField(max_length=20, blank=True)
    employment_type_after  = models.CharField(max_length=20, blank=True)
    note                   = models.TextField(blank=True, verbose_name='発令内容・理由')
    is_applied             = models.BooleanField(default=True, verbose_name='反映済み')
    applied_at             = models.DateTimeField(null=True, blank=True)
    created_by             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='+')
    created_at             = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '異動・昇格履歴'
        ordering     = ['-effective_date', '-created_at']

    def __str__(self):
        return f'{self.employee} {self.effective_date} {self.get_change_type_display()}'
