import uuid
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0004_employee_bank_account'),
    ]

    operations = [
        migrations.CreateModel(
            name='EvaluationPeriod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fiscal_year', models.PositiveSmallIntegerField(verbose_name='年度')),
                ('period_type', models.CharField(choices=[('first_half', '上期'), ('second_half', '下期')], max_length=20)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name': '評価期間', 'ordering': ['-fiscal_year', 'period_type'], 'unique_together': {('fiscal_year', 'period_type')}},
        ),
        migrations.CreateModel(
            name='EvaluationQuestion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('category', models.CharField(choices=[('performance', '業績評価'), ('competency', 'コンピテンシー評価'), ('attitude', '行動・姿勢')], max_length=20)),
                ('text', models.TextField(verbose_name='評価項目テキスト')),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'verbose_name': '評価項目', 'ordering': ['category', 'order']},
        ),
        migrations.CreateModel(
            name='Evaluation360',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='evaluation.evaluationperiod')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_evaluations', to='employees.employee', verbose_name='評価対象者')),
                ('evaluator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='given_evaluations', to='employees.employee', verbose_name='評価者')),
                ('evaluator_type', models.CharField(choices=[('self', '自己評価'), ('supervisor', '上司評価'), ('peer', '同僚評価'), ('subordinate', '部下評価')], max_length=20)),
                ('is_submitted', models.BooleanField(default=False)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('overall_comment', models.TextField(blank=True, verbose_name='総合コメント')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': '360度評価', 'unique_together': {('period', 'subject', 'evaluator')}},
        ),
        migrations.CreateModel(
            name='EvaluationScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='evaluation.evaluation360')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='evaluation.evaluationquestion')),
                ('score', models.PositiveSmallIntegerField(verbose_name='スコア（1-5）')),
                ('comment', models.TextField(blank=True)),
            ],
            options={'unique_together': {('evaluation', 'question')}},
        ),
    ]
