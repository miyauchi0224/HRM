from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('salary', '0001_initial'),
    ]

    operations = [
        # 支給明細 個別手当フィールド
        migrations.AddField(
            model_name='payslip',
            name='technical_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='技術手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='secondment_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='出向手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='housing_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='住宅手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='commute_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='通勤手当（交通費）'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='family_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='家族手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='certification_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='資格手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='position_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='役職手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='special_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='特別手当（賞与・臨時手当）'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='perfect_attendance_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='皆勤手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='diligence_allowance',
            field=models.PositiveIntegerField(default=0, verbose_name='精勤手当'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='extra_overtime_pay',
            field=models.PositiveIntegerField(default=0, verbose_name='時間外手当（深夜・休日）'),
        ),
        # 控除明細 新規フィールド
        migrations.AddField(
            model_name='payslip',
            name='nursing_insurance',
            field=models.PositiveIntegerField(default=0, verbose_name='介護保険料'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='social_insurance_total',
            field=models.PositiveIntegerField(default=0, verbose_name='社会保険料合計'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='property_savings',
            field=models.PositiveIntegerField(default=0, verbose_name='財形貯蓄'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='company_housing_fee',
            field=models.PositiveIntegerField(default=0, verbose_name='社宅・寮費'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='union_fee',
            field=models.PositiveIntegerField(default=0, verbose_name='組合費'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='mutual_aid_fee',
            field=models.PositiveIntegerField(default=0, verbose_name='共済会費'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='employee_stock_contribution',
            field=models.PositiveIntegerField(default=0, verbose_name='持株会拠出金'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='other_deductions',
            field=models.PositiveIntegerField(default=0, verbose_name='その他控除'),
        ),
        # 勤怠情報
        migrations.AddField(
            model_name='payslip',
            name='work_days',
            field=models.PositiveIntegerField(default=0, verbose_name='出勤日数'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='absence_days',
            field=models.PositiveIntegerField(default=0, verbose_name='欠勤日数'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='paid_leave_days',
            field=models.PositiveIntegerField(default=0, verbose_name='有給取得日数'),
        ),
        # 管理情報
        migrations.AddField(
            model_name='payslip',
            name='cutoff_date',
            field=models.DateField(blank=True, null=True, verbose_name='締め日'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='payment_date',
            field=models.DateField(blank=True, null=True, verbose_name='支給日'),
        ),
        migrations.AddField(
            model_name='payslip',
            name='note',
            field=models.TextField(blank=True, verbose_name='備考'),
        ),
        # Allowance.allowance_type の max_length を拡張
        migrations.AlterField(
            model_name='allowance',
            name='allowance_type',
            field=models.CharField(
                choices=[
                    ('housing', '住宅手当'), ('secondment', '出向手当'),
                    ('technical', '技術手当'), ('commute', '通勤手当'),
                    ('family', '家族手当'), ('certification', '資格手当'),
                    ('position', '役職手当'), ('special', '特別手当'),
                    ('perfect_attendance', '皆勤手当'), ('diligence', '精勤手当'),
                    ('extra_overtime', '時間外手当（深夜・休日）'), ('other', 'その他手当'),
                ],
                max_length=30,
            ),
        ),
    ]
