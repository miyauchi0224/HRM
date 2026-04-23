import uuid
from django.db import models
from apps.employees.models import Employee
from apps.common.models import SoftDeleteModel
from django.utils import timezone


class StressCheckPeriod(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, verbose_name='実施タイトル')
    start_date = models.DateField(verbose_name='回答開始日')
    end_date = models.DateField(verbose_name='回答終了日')
    is_published = models.BooleanField(default=False, verbose_name='公開済み')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'ストレスチェック実施期間'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# 57問の標準質問（セクション分け）
# A: 仕事のストレス要因(17問), B: ストレス反応(29問), C: 周囲のサポート(9問), D: 高ストレス追加(2問)
STRESS_CHECK_QUESTIONS = [
    # A: 仕事のストレス要因 (1-17)
    {'order': 1,  'section': 'A', 'text': '非常にたくさんの仕事をしなければならない',               'reverse': False},
    {'order': 2,  'section': 'A', 'text': '時間内に仕事が処理しきれない',                           'reverse': False},
    {'order': 3,  'section': 'A', 'text': '一生懸命働かなければならない',                           'reverse': False},
    {'order': 4,  'section': 'A', 'text': 'かなり注意を集中する必要がある',                         'reverse': False},
    {'order': 5,  'section': 'A', 'text': '高度の知識や技術が必要なむずかしい仕事だ',               'reverse': False},
    {'order': 6,  'section': 'A', 'text': '勤務時間中はいつも仕事のことを考えていなければならない', 'reverse': False},
    {'order': 7,  'section': 'A', 'text': 'からだを大変よく使う仕事だ',                             'reverse': False},
    {'order': 8,  'section': 'A', 'text': '自分のペースで仕事ができる',                             'reverse': True},
    {'order': 9,  'section': 'A', 'text': '自分で仕事の順番・やり方を決めることができる',           'reverse': True},
    {'order': 10, 'section': 'A', 'text': '職場の仕事の方針に自分の意見を反映できる',               'reverse': True},
    {'order': 11, 'section': 'A', 'text': '自分の技能や知識を仕事で使うことができる',               'reverse': True},
    {'order': 12, 'section': 'A', 'text': '私の部門内で意見のくい違いがある',                       'reverse': False},
    {'order': 13, 'section': 'A', 'text': '私の部門と他の部門とはうまが合わない',                   'reverse': False},
    {'order': 14, 'section': 'A', 'text': '私の職場の雰囲気は友好的である',                         'reverse': True},
    {'order': 15, 'section': 'A', 'text': '私の職場の作業環境（騒音、照明、温度、換気など）はよくない', 'reverse': False},
    {'order': 16, 'section': 'A', 'text': '仕事の内容は自分にあっている',                           'reverse': True},
    {'order': 17, 'section': 'A', 'text': '働きがいのある仕事だ',                                   'reverse': True},
    # B: ストレス反応 (18-46)
    {'order': 18, 'section': 'B', 'text': '活気がわいてくる',               'reverse': True},
    {'order': 19, 'section': 'B', 'text': '元気がいっぱいだ',               'reverse': True},
    {'order': 20, 'section': 'B', 'text': 'いきいきする',                   'reverse': True},
    {'order': 21, 'section': 'B', 'text': '怒りを感じる',                   'reverse': False},
    {'order': 22, 'section': 'B', 'text': '内心腹立たしい',                 'reverse': False},
    {'order': 23, 'section': 'B', 'text': 'イライラしている',               'reverse': False},
    {'order': 24, 'section': 'B', 'text': 'ひどく疲れた',                   'reverse': False},
    {'order': 25, 'section': 'B', 'text': 'へとへとだ',                     'reverse': False},
    {'order': 26, 'section': 'B', 'text': 'だるい',                         'reverse': False},
    {'order': 27, 'section': 'B', 'text': '気がはりつめている',             'reverse': False},
    {'order': 28, 'section': 'B', 'text': '不安だ',                         'reverse': False},
    {'order': 29, 'section': 'B', 'text': '落着かない',                     'reverse': False},
    {'order': 30, 'section': 'B', 'text': 'ゆううつだ',                     'reverse': False},
    {'order': 31, 'section': 'B', 'text': '何をするのも面倒だ',             'reverse': False},
    {'order': 32, 'section': 'B', 'text': '物事に集中できない',             'reverse': False},
    {'order': 33, 'section': 'B', 'text': '気分が晴れない',                 'reverse': False},
    {'order': 34, 'section': 'B', 'text': '仕事が手につかない',             'reverse': False},
    {'order': 35, 'section': 'B', 'text': '悲しいと感じる',                 'reverse': False},
    {'order': 36, 'section': 'B', 'text': 'めまいがする',                   'reverse': False},
    {'order': 37, 'section': 'B', 'text': '体のふしぶしが痛む',             'reverse': False},
    {'order': 38, 'section': 'B', 'text': '頭が重かったり頭痛がする',       'reverse': False},
    {'order': 39, 'section': 'B', 'text': '首筋や肩がこる',                 'reverse': False},
    {'order': 40, 'section': 'B', 'text': '腰が痛い',                       'reverse': False},
    {'order': 41, 'section': 'B', 'text': '目が疲れる',                     'reverse': False},
    {'order': 42, 'section': 'B', 'text': '動悸や息切れがする',             'reverse': False},
    {'order': 43, 'section': 'B', 'text': '胃腸の具合が悪い',               'reverse': False},
    {'order': 44, 'section': 'B', 'text': '食欲がない',                     'reverse': False},
    {'order': 45, 'section': 'B', 'text': '眠れない',                       'reverse': False},
    {'order': 46, 'section': 'B', 'text': 'この頃仕事への意欲が失せてきている', 'reverse': False},
    # C: 周囲のサポート (47-55)
    {'order': 47, 'section': 'C', 'text': '上司に気軽に話しができる',                       'reverse': True},
    {'order': 48, 'section': 'C', 'text': '上司はあなたが困ったときに、きちんと対応してくれる', 'reverse': True},
    {'order': 49, 'section': 'C', 'text': '上司からの仕事上の援助が得られる',               'reverse': True},
    {'order': 50, 'section': 'C', 'text': '同僚に気軽に話ができる',                         'reverse': True},
    {'order': 51, 'section': 'C', 'text': '同僚はあなたが困ったときに助けてくれる',         'reverse': True},
    {'order': 52, 'section': 'C', 'text': '同僚からの仕事上の援助が得られる',               'reverse': True},
    {'order': 53, 'section': 'C', 'text': '家族や友人はあなたが困ったときに助けてくれる',   'reverse': True},
    {'order': 54, 'section': 'C', 'text': '家族や友人と気軽に話ができる',                   'reverse': True},
    {'order': 55, 'section': 'C', 'text': '配偶者（パートナー）の理解や協力が得られる',     'reverse': True},
    # D: 満足度 (56-57)
    {'order': 56, 'section': 'D', 'text': '仕事に満足だ',     'reverse': True},
    {'order': 57, 'section': 'D', 'text': '家庭生活に満足だ', 'reverse': True},
]


class StressCheckResponse(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.ForeignKey(
        StressCheckPeriod,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='stress_check_responses',
    )
    answers = models.JSONField(default=dict, verbose_name='回答（問番号→スコア1-4）')
    submitted_at = models.DateTimeField(null=True, blank=True)
    is_submitted = models.BooleanField(default=False)
    high_stress = models.BooleanField(default=False, verbose_name='高ストレス')
    total_score = models.IntegerField(default=0, verbose_name='合計スコア')

    class Meta:
        verbose_name = 'ストレスチェック回答'
        unique_together = [['period', 'employee']]

    def __str__(self):
        return f'{self.employee} - {self.period}'

    def calculate_score(self):
        """高ストレス判定（57問スコア集計）"""
        score = 0
        for q in STRESS_CHECK_QUESTIONS:
            ans = self.answers.get(str(q['order']), 0)
            if q['reverse']:
                score += (5 - ans)
            else:
                score += ans
        self.total_score = score
        # 高ストレス判定: 77点以上（仕事のストレス要因が高く心身反応も高い場合）
        self.high_stress = score >= 77
        return score
