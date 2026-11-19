"""
パルスサーベイの回答保存と集計（詳細設計書 7.10）
"""
import random
from collections import defaultdict

from django.conf import settings
from django.db import transaction

from .models import PulseParticipation, PulseQuestion, PulseResponse


class AnswerError(Exception):
    pass


def clean_answers(survey, raw: dict) -> dict:
    """回答を検証して {question_id: 値} にそろえる"""
    if not isinstance(raw, dict):
        raise AnswerError('回答の形式が正しくありません')
    cleaned = {}
    for q in survey.questions.all():
        value = raw.get(str(q.id))
        if value in (None, ''):
            if q.is_required:
                raise AnswerError(f'「{q.text}」に回答してください')
            continue
        if q.kind == PulseQuestion.Kind.TEXT:
            text = str(value).strip()[:2000]
            if text:
                cleaned[str(q.id)] = text
            continue
        try:
            n = int(value)
        except (TypeError, ValueError):
            raise AnswerError(f'「{q.text}」の回答が正しくありません')
        lo, hi = (1, 5) if q.kind == PulseQuestion.Kind.SCALE5 else (0, 10)
        if not lo <= n <= hi:
            raise AnswerError(f'「{q.text}」は {lo}〜{hi} で回答してください')
        cleaned[str(q.id)] = n
    return cleaned


@transaction.atomic
def submit_answers(survey, employee, raw: dict):
    if PulseParticipation.objects.select_for_update().filter(survey=survey, employee=employee).exists():
        raise AnswerError('このサーベイには回答済みです')
    answers = clean_answers(survey, raw)
    PulseParticipation.objects.create(survey=survey, employee=employee)
    PulseResponse.objects.create(
        survey=survey, answers=answers, department=employee.department,
        employee=None if survey.is_anonymous else employee,
    )


def _numeric_summary(question, values):
    if question.kind == PulseQuestion.Kind.SCALE5:
        dist = {str(i): 0 for i in range(1, 6)}
        for v in values:
            dist[str(v)] += 1
        return {'average': round(sum(values) / len(values), 2) if values else None, 'distribution': dist}

    dist = {str(i): 0 for i in range(0, 11)}
    for v in values:
        dist[str(v)] += 1
    n = len(values)
    promoters  = sum(1 for v in values if v >= 9)
    detractors = sum(1 for v in values if v <= 6)
    return {
        'average':      round(sum(values) / n, 2) if n else None,
        'enps':         round((promoters - detractors) / n * 100) if n else None,
        'promoters':    promoters,
        'passives':     n - promoters - detractors,
        'detractors':   detractors,
        'distribution': dist,
    }


def build_results(survey) -> dict:
    """集計。最小人数未満の集団（全体・部署）は数値を出さない"""
    min_size  = settings.PULSE_MIN_GROUP_SIZE
    responses = list(survey.responses.all())
    total     = len(responses)
    base = {'survey_id': str(survey.id), 'title': survey.title, 'response_count': total,
            'min_group_size': min_size}
    if total < min_size:
        return {**base, 'insufficient': True, 'questions': [], 'departments': []}

    questions = list(survey.questions.all())
    numeric   = [q for q in questions if q.kind != PulseQuestion.Kind.TEXT]
    q_results = []
    for q in questions:
        values = [r.answers[str(q.id)] for r in responses if str(q.id) in r.answers]
        item = {'id': str(q.id), 'text': q.text, 'kind': q.kind, 'answer_count': len(values)}
        if q.kind == PulseQuestion.Kind.TEXT:
            comments = list(values)
            random.shuffle(comments)  # 回答順から個人を推測されないようにする
            item['comments'] = comments
        else:
            item.update(_numeric_summary(q, values))
        q_results.append(item)

    by_dept = defaultdict(list)
    for r in responses:
        by_dept[r.department or '（部署なし）'].append(r)
    departments = []
    for dept, rs in sorted(by_dept.items()):
        if len(rs) < min_size:
            departments.append({'department': dept, 'insufficient': True})
            continue
        averages = {}
        for q in numeric:
            vals = [r.answers[str(q.id)] for r in rs if str(q.id) in r.answers]
            averages[str(q.id)] = round(sum(vals) / len(vals), 2) if vals else None
        departments.append({'department': dept, 'response_count': len(rs), 'averages': averages})

    return {**base, 'insufficient': False, 'questions': q_results, 'departments': departments}
