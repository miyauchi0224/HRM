from pathlib import Path
from decouple import config, Csv
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost', cast=Csv())

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    # 'simple_history',  # pip install django-simple-history 後に有効化
]

LOCAL_APPS = [
    'apps.common',
    'apps.accounts',
    'apps.employees',
    'apps.attendance',
    'apps.leave',
    'apps.mbo',
    'apps.salary',
    'apps.expense',
    'apps.skills',
    'apps.notifications',
    'apps.todo',
    'apps.intra',
    'apps.approval',
    'apps.chat',
    'apps.recruitment',
    'apps.assets',
    'apps.evaluation',
    'apps.learning',
    'apps.analytics',
    'apps.ai_assistant',
    'apps.onboarding',
    'apps.documents',
    'apps.stress_check',
    'apps.calendar_sync',
    'apps.compliance',
    'apps.scheduler',
    'apps.health_checkup',
    'apps.one_on_one',
    'apps.pulse_survey',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'apps.common.middleware.MediaSecurityHeadersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'simple_history.middleware.HistoryRequestMiddleware',  # pip install django-simple-history 後に有効化
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='hrm'),
        'USER': config('DB_USER', default='hrm_admin'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'ja'
TIME_ZONE = 'Asia/Tokyo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── REST Framework ──────────────────────────────────────────────
REST_FRAMEWORK = {
    # HttpOnly Cookie の JWT で認証（Bearer ヘッダーも可）。Cookie 利用時は CSRF を検証する
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.accounts.authentication.CookieJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'config.pagination.StandardPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_RATES': {
        'login': config('LOGIN_RATE', default='10/min'),
    },
}

# ── JWT 設定 ─────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ── CORS ─────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000', cast=Csv())
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default=','.join(CORS_ALLOWED_ORIGINS), cast=Csv())

# ── 認証 Cookie・ログイン制限（v1.3） ─────────────────────────────
AUTH_COOKIE_ACCESS       = 'hrm_access'
AUTH_COOKIE_REFRESH      = 'hrm_refresh'
AUTH_COOKIE_REFRESH_PATH = '/api/v1/auth/'
AUTH_COOKIE_SECURE       = config('AUTH_COOKIE_SECURE', default=not DEBUG, cast=bool)
AUTH_COOKIE_SAMESITE     = 'Lax'
AUTH_COOKIE_DOMAIN       = config('AUTH_COOKIE_DOMAIN', default='')
CSRF_COOKIE_SAMESITE     = 'Lax'
CSRF_COOKIE_SECURE       = AUTH_COOKIE_SECURE
CSRF_COOKIE_DOMAIN       = AUTH_COOKIE_DOMAIN or None
SESSION_COOKIE_SECURE    = AUTH_COOKIE_SECURE
LOGIN_MAX_FAILURES       = config('LOGIN_MAX_FAILURES', default=5, cast=int)
LOGIN_LOCK_MINUTES       = config('LOGIN_LOCK_MINUTES', default=15, cast=int)

# 外部サービスの認証情報を暗号化する鍵（Fernet 形式）。未設定なら SECRET_KEY から導出（開発用）
FIELD_ENCRYPTION_KEY     = config('FIELD_ENCRYPTION_KEY', default='')

# ── 本番用のセキュリティ設定（DEBUG=False のとき有効） ────────────────
X_FRAME_OPTIONS        = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
if not DEBUG:
    SECURE_SSL_REDIRECT            = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS            = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # ヘルスチェックはロードバランサーから HTTP で来るため HTTPS へのリダイレクト対象外
    SECURE_REDIRECT_EXEMPT         = [r'^api/v1/health/$']

# ── AWS ──────────────────────────────────────────────────────────
AWS_REGION = config('AWS_REGION', default='ap-northeast-1')
S3_STORAGE_BUCKET = config('S3_STORAGE_BUCKET', default='')
S3_TEMPLATE_BUCKET = config('S3_TEMPLATE_BUCKET', default='')
BEDROCK_MODEL_ID = config('BEDROCK_MODEL_ID', default='anthropic.claude-sonnet-4-5-20250929-v1:0')
ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY', default='')

# ── API ドキュメント (drf-spectacular) ───────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'HRM API',
    'DESCRIPTION': '人事管理システム API',
    'VERSION': '1.0.0',
    # 本番では API ドキュメントを管理者（is_staff）だけに公開する
    'SERVE_PERMISSIONS': (
        ['rest_framework.permissions.AllowAny'] if DEBUG
        else ['rest_framework.permissions.IsAdminUser']
    ),
}

# ── OAuth 設定（Microsoft / Google） ──────────────────────────────
MICROSOFT_CLIENT_ID = config('MICROSOFT_CLIENT_ID', default='')
MICROSOFT_CLIENT_SECRET = config('MICROSOFT_CLIENT_SECRET', default='')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')

# ── 運用強化機能（v1.1） ──────────────────────────────────────────
SCHEDULER_RUN_AT              = config('SCHEDULER_RUN_AT', default='06:00')
APPROVAL_REMIND_DAYS          = config('APPROVAL_REMIND_DAYS', default=3, cast=int)
WORK_INTERVAL_MINUTES         = config('WORK_INTERVAL_MINUTES', default=660, cast=int)
COMPENSATORY_LEAVE_VALID_DAYS = config('COMPENSATORY_LEAVE_VALID_DAYS', default=90, cast=int)
PULSE_MIN_GROUP_SIZE          = config('PULSE_MIN_GROUP_SIZE', default=5, cast=int)
FRONTEND_URL                  = config('FRONTEND_URL', default='http://localhost:3000')
WEBHOOK_TIMEOUT_SECONDS       = config('WEBHOOK_TIMEOUT_SECONDS', default=5, cast=int)
WEBHOOK_ASYNC                 = config('WEBHOOK_ASYNC', default=True, cast=bool)  # テストでは False にして同期送信
