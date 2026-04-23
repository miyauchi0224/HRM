from django.apps import AppConfig


class StressCheckConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stress_check'
    verbose_name = 'ストレスチェック'
