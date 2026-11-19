from datetime import date

from django.core.management.base import BaseCommand, CommandError

from apps.scheduler.runner import run_due_jobs


class Command(BaseCommand):
    help = '定期ジョブを1回実行する（cron / EventBridge Scheduler から起動する想定）'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='対象日（YYYY-MM-DD）。省略時は今日')
        parser.add_argument('--job', help='指定したジョブだけ実行する（例: leave.grant_annual_leave）')
        parser.add_argument('--force', action='store_true', help='その日に成功済みのジョブも再実行する')

    def handle(self, *args, **options):
        run_date = None
        if options['date']:
            try:
                run_date = date.fromisoformat(options['date'])
            except ValueError:
                raise CommandError('--date は YYYY-MM-DD 形式で指定してください')

        try:
            runs = run_due_jobs(run_date=run_date, only=options['job'], force=options['force'])
        except ValueError as e:
            raise CommandError(str(e))

        if not runs:
            self.stdout.write('実行対象のジョブはありません（本日分は実行済み）')
        for run in runs:
            style = self.style.SUCCESS if run.status == 'success' else self.style.ERROR
            self.stdout.write(style(f'{run.job_name}: {run.status} {run.result or ""}'))
