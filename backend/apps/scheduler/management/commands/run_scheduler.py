import time
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from apps.scheduler.runner import run_due_jobs


class Command(BaseCommand):
    help = '常駐して毎日 SCHEDULER_RUN_AT に定期ジョブを実行する（docker compose の scheduler サービス用）'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=60, help='時刻を確認する間隔（秒）')

    def handle(self, *args, **options):
        run_at = datetime.strptime(settings.SCHEDULER_RUN_AT, '%H:%M').time()
        self.stdout.write(f'スケジューラを起動しました（毎日 {run_at:%H:%M} に実行）')

        while True:
            now = timezone.localtime()
            # 実行時刻を過ぎていれば当日分を実行（成功済みのジョブは runner 側でスキップされる）
            if now.time() >= run_at:
                close_old_connections()
                for run in run_due_jobs(run_date=now.date()):
                    self.stdout.write(f'{now:%Y-%m-%d %H:%M} {run.job_name}: {run.status}')
                close_old_connections()
            time.sleep(options['interval'])
