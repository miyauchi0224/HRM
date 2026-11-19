from django.apps import AppConfig


class HealthCheckupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.health_checkup'
    verbose_name = '健康診断'
