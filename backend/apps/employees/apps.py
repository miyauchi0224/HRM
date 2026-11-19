from django.apps import AppConfig

class EmployeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.employees'

    def ready(self):
        import apps.employees.history  # noqa: F401  異動・昇格履歴のシグナル登録
