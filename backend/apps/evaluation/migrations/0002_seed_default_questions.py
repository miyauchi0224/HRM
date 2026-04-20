"""
360度評価のデフォルト評価項目を投入するデータマイグレーション。
①業務遂行 ②主体性 ③学習姿勢 ④対人配慮 ⑤チーム貢献
⑥リーダー向け ⑦倫理 ⑧創造性 ⑨外部対応（該当者のみ）
"""
from django.db import migrations


DEFAULT_QUESTIONS = [
    # ① 業務遂行・仕事の進め方
    {'category': 'performance', 'order': 1,  'text': '【業務遂行】計画性・段取り力がある'},
    {'category': 'performance', 'order': 2,  'text': '【業務遂行】優先順位の付け方が適切である'},
    {'category': 'performance', 'order': 3,  'text': '【業務遂行】期限・約束を遵守している'},
    {'category': 'performance', 'order': 4,  'text': '【業務遂行】業務の正確性・丁寧さがある'},
    {'category': 'performance', 'order': 5,  'text': '【業務遂行】改善提案・工夫を積極的に行う'},

    # ② 主体性・自律性
    {'category': 'competency', 'order': 10, 'text': '【主体性】指示待ちにならず自ら行動できる'},
    {'category': 'competency', 'order': 11, 'text': '【主体性】自分の役割を理解して動いている'},
    {'category': 'competency', 'order': 12, 'text': '【主体性】課題を自分事として捉えている'},
    {'category': 'competency', 'order': 13, 'text': '【主体性】困難に直面したときに粘り強く取り組む'},

    # ③ 学習姿勢・成長意欲
    {'category': 'competency', 'order': 20, 'text': '【学習姿勢】新しい知識・スキルを積極的に学ぶ'},
    {'category': 'competency', 'order': 21, 'text': '【学習姿勢】フィードバックを素直に受け入れる'},
    {'category': 'competency', 'order': 22, 'text': '【学習姿勢】自己改善に継続的に取り組んでいる'},
    {'category': 'competency', 'order': 23, 'text': '【学習姿勢】失敗から学び次に活かしている'},

    # ④ 対人配慮・感情面（EQ）
    {'category': 'attitude', 'order': 30, 'text': '【対人配慮】他者の立場を考えた対応ができる'},
    {'category': 'attitude', 'order': 31, 'text': '【対人配慮】感情をコントロールして行動できる'},
    {'category': 'attitude', 'order': 32, 'text': '【対人配慮】周囲への気配りができている'},
    {'category': 'attitude', 'order': 33, 'text': '【対人配慮】衝突・対立時に冷静に対処できる'},

    # ⑤ チーム・組織への貢献
    {'category': 'attitude', 'order': 40, 'text': '【チーム貢献】情報を積極的に共有している'},
    {'category': 'attitude', 'order': 41, 'text': '【チーム貢献】他メンバーを支援・サポートしている'},
    {'category': 'attitude', 'order': 42, 'text': '【チーム貢献】チーム全体の視点で行動している'},
    {'category': 'attitude', 'order': 43, 'text': '【チーム貢献】組織ルール・方針を尊重している'},

    # ⑥ リーダー・管理職向け
    {'category': 'competency', 'order': 50, 'text': '【リーダー】メンバーの育成・指導を適切に行っている'},
    {'category': 'competency', 'order': 51, 'text': '【リーダー】公平性を保ち、えこひいきをしない'},
    {'category': 'competency', 'order': 52, 'text': '【リーダー】判断力・意思決定の質が高い'},
    {'category': 'competency', 'order': 53, 'text': '【リーダー】自分の責任を明確にして行動している'},
    {'category': 'competency', 'order': 54, 'text': '【リーダー】チームの心理的安全性を高めている'},

    # ⑦ 倫理・コンプライアンス
    {'category': 'attitude', 'order': 60, 'text': '【倫理】誠実に行動している'},
    {'category': 'attitude', 'order': 61, 'text': '【倫理】情報管理・守秘義務を適切に守っている'},
    {'category': 'attitude', 'order': 62, 'text': '【倫理】公平性・透明性のある行動をとっている'},
    {'category': 'attitude', 'order': 63, 'text': '【倫理】ハラスメントを起こさない言動・行動をとっている'},

    # ⑧ 創造性・問題解決（研究・技術系向け）
    {'category': 'performance', 'order': 70, 'text': '【創造性】問題発見力・課題設定力がある'},
    {'category': 'performance', 'order': 71, 'text': '【創造性】仮説立案・思考の柔軟性がある'},
    {'category': 'performance', 'order': 72, 'text': '【創造性】新しい視点・アイデアを積極的に提示する'},
    {'category': 'performance', 'order': 73, 'text': '【創造性】試行錯誤・実験的な取り組みに前向きである'},

    # ⑨ 外部対応・社会性（該当者のみ）
    {'category': 'competency', 'order': 80, 'text': '【外部対応】外部関係者（顧客・取引先）と適切に対応できる'},
    {'category': 'competency', 'order': 81, 'text': '【外部対応】説明が分かりやすく、相手に伝わっている'},
    {'category': 'competency', 'order': 82, 'text': '【外部対応】調整力・交渉姿勢が適切である'},
    {'category': 'competency', 'order': 83, 'text': '【外部対応】組織の代表として適切な振る舞いができている'},
]


def seed_questions(apps, schema_editor):
    EvaluationQuestion = apps.get_model('evaluation', 'EvaluationQuestion')
    if EvaluationQuestion.objects.exists():
        return  # 既にデータがある場合はスキップ
    for q in DEFAULT_QUESTIONS:
        EvaluationQuestion.objects.create(**q)


def unseed_questions(apps, schema_editor):
    EvaluationQuestion = apps.get_model('evaluation', 'EvaluationQuestion')
    texts = [q['text'] for q in DEFAULT_QUESTIONS]
    EvaluationQuestion.objects.filter(text__in=texts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_questions, unseed_questions),
    ]
