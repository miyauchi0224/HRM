import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel


class Skill(SoftDeleteModel):
    class Category(models.TextChoices):
        LANGUAGE    = 'language',    'プログラミング言語'
        FRAMEWORK   = 'framework',   'フレームワーク'
        INFRA       = 'infra',       'インフラ'
        MANAGEMENT  = 'management',  'マネジメント'
        LANGUAGE_KI = 'lang_spoken', '語学'
        CERTIFICATE = 'certificate', '資格'
        OTHER       = 'other',       'その他'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee       = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='skills')
    skill_name     = models.CharField(max_length=100, verbose_name='スキル名')
    category       = models.CharField(max_length=20, choices=Category.choices)
    level          = models.CharField(max_length=50, blank=True, verbose_name='レベル')
    organizer      = models.CharField(max_length=100, blank=True, verbose_name='主催者・発行機関')
    certified_date = models.DateField(null=True, blank=True, verbose_name='取得日')
    expiry_date    = models.DateField(null=True, blank=True, verbose_name='有効期限')
    note           = models.TextField(blank=True, verbose_name='備考')

    class Meta:
        verbose_name = 'スキル'
        ordering     = ['category', 'skill_name']
