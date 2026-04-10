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
        EMPLOYEE = 'employee', '社員'
        MANAGER  = 'manager',  '管理職'
        HR       = 'hr',       '人事担当'
        ADMIN    = 'admin',    'システム管理者'

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email        = models.EmailField(unique=True)
    cognito_sub  = models.CharField(max_length=255, unique=True, blank=True, null=True)
    role         = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name      = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email

    # ロール確認ヘルパー
    @property
    def is_manager(self):
        return self.role in (self.Role.MANAGER, self.Role.HR, self.Role.ADMIN)

    @property
    def is_hr(self):
        return self.role in (self.Role.HR, self.Role.ADMIN)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
