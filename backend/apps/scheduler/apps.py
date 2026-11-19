from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scheduler'
    verbose_name = '定期実行'

    def ready(self):
        # 各アプリの jobs.py を読み込んでジョブを登録する
        from django.utils.module_loading import autodiscover_modules
        autodiscover_modules('jobs')
