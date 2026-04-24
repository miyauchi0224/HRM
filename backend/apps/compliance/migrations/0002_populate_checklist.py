# Generated migration to populate checklist data

from django.db import migrations


def populate_checklist(apps, schema_editor):
    """attention.mdからチェックリストデータを生成"""
    ComplianceChecklistSection = apps.get_model('compliance', 'ComplianceChecklistSection')
    ComplianceChecklistItem = apps.get_model('compliance', 'ComplianceChecklistItem')

    checklist_data = [
        {
            'title': '健康診断',
            'items': [
                '年1回の定期健康診断を実施している',
                '対象者（週30時間以上等）を正しく抽出している',
                '健診費用を会社が負担している',
                '未受診者に対して受診勧奨を行っている',
                '健診結果を回収している',
                '健診結果を5年間保存している',
                '要再検査・要精密検査者を把握している',
                '必要に応じて就業制限を実施している',
            ],
        },
        {
            'title': '労働時間管理',
            'items': [
                '労働時間を客観的に記録している（打刻・ログ等）',
                '勤怠記録の修正履歴を保存している',
                '月次で労働時間を確認している',
                '36協定の範囲内で運用している',
                '月45時間超の従業員を把握している',
                '月80時間超の従業員に対応している',
            ],
        },
        {
            'title': '時間外労働管理',
            'items': [
                '時間外労働の事前申請制度がある',
                '上長承認フローが存在する',
                '無断残業を把握している',
                '実労働時間に基づき賃金を支払っている',
            ],
        },
        {
            'title': '有給休暇管理',
            'items': [
                '年次有給休暇の付与日を管理している',
                '有給取得日数を管理している',
                '年5日の取得義務を満たしている',
                '未取得者への取得促進を行っている',
            ],
        },
        {
            'title': '安全配慮義務',
            'items': [
                '長時間労働者への対応を行っている',
                '過重労働防止措置を実施している',
                'メンタルヘルス不調者への配慮がある',
            ],
        },
        {
            'title': 'ストレスチェック',
            'items': [
                '実施対象人数を把握している',
                '必要に応じてストレスチェックを実施している',
                '実施結果を適切に管理している',
            ],
        },
        {
            'title': '就業制限・配置転換',
            'items': [
                '医師意見に基づく就業制限を実施している',
                '必要に応じて配置転換を行っている',
                '健康状態に応じた業務調整を行っている',
            ],
        },
        {
            'title': '情報管理（健康情報）',
            'items': [
                '健康診断結果を適切に管理している',
                '閲覧権限を制限している',
                '個人情報として適切に保護している',
            ],
        },
        {
            'title': '記録保存',
            'items': [
                '健康診断結果を5年間保存している',
                '勤怠記録を3年間保存している',
                '賃金台帳を5年間保存している',
                '各種記録の改ざん防止措置がある',
            ],
        },
        {
            'title': '教育・周知',
            'items': [
                '就業規則を従業員に周知している',
                '労務ルールを説明している',
                '健康管理に関する教育を実施している',
            ],
        },
        {
            'title': '最低限の必須運用（小規模企業）',
            'items': [
                '健康診断（年1回）を実施している',
                '労働時間を記録している',
                '有給休暇を管理している',
                '長時間労働を把握している',
                '記録を保存している',
            ],
        },
        {
            'title': 'リスクチェック（重要）',
            'items': [
                '健診未受診者を放置していない',
                '月80時間超の残業を放置していない',
                '有給未取得を放置していない',
                '勤怠記録が曖昧になっていない',
            ],
            'critical_indices': [0, 1, 2, 3],
        },
    ]

    for section_order, section_data in enumerate(checklist_data, start=1):
        section = ComplianceChecklistSection.objects.create(
            title=section_data['title'],
            order=section_order,
        )

        critical_indices = section_data.get('critical_indices', [])
        for item_order, item_title in enumerate(section_data['items'], start=1):
            is_critical = (item_order - 1) in critical_indices
            ComplianceChecklistItem.objects.create(
                section=section,
                title=item_title,
                order=item_order,
                is_critical=is_critical,
            )


def reverse_checklist(apps, schema_editor):
    """ロールバック時のデータ削除"""
    ComplianceChecklistSection = apps.get_model('compliance', 'ComplianceChecklistSection')
    ComplianceChecklistSection.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_checklist, reverse_checklist),
    ]
