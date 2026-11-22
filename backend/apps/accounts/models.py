import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.fields import EncryptedTextField


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
        MANAGER    = 'manager',    '管理職'
        HR         = 'hr',         '人事'
        LABOR      = 'labor',      '労務'
        ACCOUNTING = 'accounting', '経理'
        CUSTOMER   = 'customer',   '顧客'
        ADMIN      = 'admin',      'システム管理者'

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email              = models.EmailField(unique=True)
    cognito_sub        = models.CharField(max_length=255, unique=True, blank=True, null=True)
    role               = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    roles              = models.JSONField(default=list, blank=True, verbose_name='ロール（複数）')
    class AIProvider(models.TextChoices):
        ANTHROPIC = 'anthropic', 'Anthropic (Claude)'
        OPENAI    = 'openai',    'OpenAI (ChatGPT)'

    # 外部サービスの認証情報は暗号化して保存する（v1.3）
    anthropic_api_key  = EncryptedTextField(blank=True, verbose_name='Anthropic APIキー')
    openai_api_key     = EncryptedTextField(blank=True, verbose_name='OpenAI APIキー')
    ai_provider        = models.CharField(
        max_length=20, choices=AIProvider.choices, default=AIProvider.ANTHROPIC,
        verbose_name='使用するAIプロバイダー',
    )
    class WebhookProvider(models.TextChoices):
        SLACK = 'slack', 'Slack'
        TEAMS = 'teams', 'Microsoft Teams'

    # 本人宛て通知の転送先（Slack / Teams の Incoming Webhook）
    personal_webhook_provider = models.CharField(
        max_length=10, choices=WebhookProvider.choices, blank=True, verbose_name='個人通知の転送先',
    )
    personal_webhook_url = EncryptedTextField(blank=True, verbose_name='個人通知の Webhook URL')

    # ログイン試行の制限（v1.3）
    failed_login_count = models.PositiveIntegerField(default=0, verbose_name='連続ログイン失敗回数')
    locked_until       = models.DateTimeField(null=True, blank=True, verbose_name='ロック解除日時')
    # これより前に発行されたトークンは無効（パスワード変更で全端末をログアウトさせる）
    password_changed_at = models.DateTimeField(null=True, blank=True, verbose_name='パスワード変更日時')
    # 初期パスワード（生年月日など）のままのアカウント。ログイン後にパスワード変更を求める
    must_change_password = models.BooleanField(default=False, verbose_name='パスワード変更が必要')
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

    def save(self, *args, **kwargs):
        """roles と role を同期（roles が主、role は互換性のため）"""
        if not self.roles and self.role:
            self.roles = [self.role]
        elif self.roles:
            self.role = self.roles[0]
        super().save(*args, **kwargs)

    # ===== ロール確認ヘルパー =====

    @property
    def is_supervisor(self):
        """
        上司レベル以上（直属部下の勤怠・休暇・MBOの参照・承認が可能）
        manager / hr / accounting / admin が対象（supervisor ロール廃止により manager 以上）
        """
        return any(r in self.roles for r in (
            self.Role.MANAGER, self.Role.HR, self.Role.ACCOUNTING, self.Role.ADMIN,
        ))

    @property
    def is_manager(self):
        """
        管理職以上（全社員データの参照、イントラ全記事閲覧が可能）
        manager / hr / accounting / admin が対象
        ※ supervisor は部下のみ参照可のため含まない
        """
        return any(r in self.roles for r in (
            self.Role.MANAGER, self.Role.HR, self.Role.ACCOUNTING, self.Role.ADMIN,
        ))

    @property
    def is_hr(self):
        """
        人事以上（社員マスタ編集・給与等級・手当管理が可能）
        hr / admin が対象
        """
        return any(r in self.roles for r in (self.Role.HR, self.Role.ADMIN))

    @property
    def is_accounting(self):
        """
        経理以上（給与計算・勘定科目管理・経費承認が可能）
        accounting / hr / admin が対象
        ※ 人事も給与関連を扱うため含む
        """
        return any(r in self.roles for r in (self.Role.ACCOUNTING, self.Role.HR, self.Role.ADMIN))

    @property
    def is_labor(self):
        """
        労務以上（健康診断・年5日取得状況など労務管理データを扱える）
        labor / hr / admin が対象
        """
        return any(r in self.roles for r in (self.Role.LABOR, self.Role.HR, self.Role.ADMIN))

    @property
    def is_admin(self):
        """システム管理者のみ（Django管理画面へのアクセス権）"""
        return self.Role.ADMIN in self.roles

    @property
    def is_customer(self):
        """顧客（社内の勤怠・給与等を閲覧不可、イントラ公開記事・通知のみ）"""
        return self.Role.CUSTOMER in self.roles

    def set_password(self, raw_password):
        super().set_password(raw_password)
        if not self._state.adding:
            self.password_changed_at = timezone.now()

    # ── ログイン試行の制限 ──────────────────────────────
    @property
    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())

    def register_login_failure(self, max_failures, lock_minutes):
        """ログイン失敗を記録し、上限に達したらロックする。ロックしたら True"""
        from datetime import timedelta
        self.failed_login_count += 1
        locked = False
        if self.failed_login_count >= max_failures:
            self.locked_until = timezone.now() + timedelta(minutes=lock_minutes)
            self.failed_login_count = 0
            locked = True
        self.save(update_fields=['failed_login_count', 'locked_until'])
        return locked

    def reset_login_failures(self):
        if self.failed_login_count or self.locked_until:
            self.failed_login_count = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_count', 'locked_until'])
