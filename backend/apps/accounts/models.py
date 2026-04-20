import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        EMPLOYEE   = 'employee',   '社員'
        SUPERVISOR = 'supervisor', '上司'
        MANAGER    = 'manager',    '管理職'
        HR         = 'hr',         '人事'
        ACCOUNTING = 'accounting', '経理'
        CUSTOMER   = 'customer',   '顧客'
        ADMIN      = 'admin',      'システム管理者'

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email              = models.EmailField(unique=True)
    cognito_sub        = models.CharField(max_length=255, unique=True, blank=True, null=True)
    role               = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    anthropic_api_key  = models.CharField(max_length=200, blank=True, verbose_name='Anthropic APIキー')
    is_active          = models.BooleanField(default=True)
    is_staff           = models.BooleanField(default=False)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name        = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email

    # ===== ロール確認ヘルパー =====

    @property
    def is_supervisor(self):
        """
        上司レベル以上（直属部下の勤怠・休暇・MBOの参照・承認が可能）
        supervisor / manager / hr / accounting / admin が対象
        """
        return self.role in (
            self.Role.SUPERVISOR, self.Role.MANAGER,
            self.Role.HR, self.Role.ACCOUNTING, self.Role.ADMIN,
        )

    @property
    def is_manager(self):
        """
        管理職以上（全社員データの参照、イントラ全記事閲覧が可能）
        manager / hr / accounting / admin が対象
        ※ supervisor は部下のみ参照可のため含まない
        """
        return self.role in (
            self.Role.MANAGER, self.Role.HR, self.Role.ACCOUNTING, self.Role.ADMIN,
        )

    @property
    def is_hr(self):
        """
        人事以上（社員マスタ編集・給与等級・手当管理が可能）
        hr / admin が対象
        """
        return self.role in (self.Role.HR, self.Role.ADMIN)

    @property
    def is_accounting(self):
        """
        経理以上（給与計算・勘定科目管理・経費承認が可能）
        accounting / hr / admin が対象
        ※ 人事も給与関連を扱うため含む
        """
        return self.role in (self.Role.ACCOUNTING, self.Role.HR, self.Role.ADMIN)

    @property
    def is_admin(self):
        """システム管理者のみ（Django管理画面へのアクセス権）"""
        return self.role == self.Role.ADMIN

    @property
    def is_customer(self):
        """顧客（社内の勤怠・給与等を閲覧不可、イントラ公開記事・通知のみ）"""
        return self.role == self.Role.CUSTOMER
