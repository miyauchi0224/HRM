import uuid
from django.db import models
from apps.accounts.models import User


class Employee(models.Model):
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
    first_name        = models.CharField(max_length=50, verbose_name='名')
    last_name_kana    = models.CharField(max_length=50, verbose_name='姓（カナ）')
    first_name_kana   = models.CharField(max_length=50, verbose_name='名（カナ）')
    birth_date        = models.DateField(verbose_name='生年月日')
    gender            = models.CharField(max_length=10, choices=Gender.choices, verbose_name='性別')
    hire_date         = models.DateField(verbose_name='入社日')
    retire_date       = models.DateField(null=True, blank=True, verbose_name='退職日')
    department        = models.CharField(max_length=100, verbose_name='部署')
    position          = models.CharField(max_length=100, verbose_name='役職')
    grade             = models.PositiveIntegerField(default=1, verbose_name='等級')
    employment_type   = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    phone             = models.CharField(max_length=20, blank=True, verbose_name='電話番号')
    personal_email    = models.EmailField(blank=True, verbose_name='個人メール')
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


class EmergencyContact(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee     = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='emergency_contacts')
    name         = models.CharField(max_length=100, verbose_name='氏名')
    relationship = models.CharField(max_length=50, verbose_name='続柄')
    phone        = models.CharField(max_length=20, verbose_name='電話番号')
    sort_order   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']


class FamilyMember(models.Model):
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
