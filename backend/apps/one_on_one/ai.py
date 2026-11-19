"""
1on1 の AI 要約（詳細設計書 7.7）

anthropic SDK 0.40 には output_config / fallbacks の引数がないため extra_body で送り、
応答は SDK の型に頼らず生の JSON から読む（新しいブロック種別が来ても壊れないように）。
"""
import json

import anthropic

from apps.ai_assistant.views import get_client

MODEL = 'claude-opus-5-5'

SUMMARY_SCHEMA = {
    'type': 'object',
    'properties': {
        'summary': {'type': 'string'},
        'action_items': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'text':  {'type': 'string'},
                    'owner': {'type': 'string', 'enum': ['manager', 'member']},
                },
                'required': ['text', 'owner'],
                'additionalProperties': False,
            },
        },
        'next_agenda': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['summary', 'action_items', 'next_agenda'],
    'additionalProperties': False,
}

SYSTEM_PROMPT = """あなたは上司と部下の1on1ミーティングの記録係です。
渡されたアジェンダとメモから、次の3つを日本語で作成してください。

- summary: 話した内容と決まったことの要約（300字程度）。メモに書かれていないことは推測で補わない。
- action_items: 次回までに誰が何をするか。owner は上司なら "manager"、部下なら "member"。メモから読み取れるものだけを挙げる。
- next_agenda: 次回の1on1で扱うとよい話題を2〜4件。前回のアクションアイテムの進捗確認を含める。"""


class AISummaryError(Exception):
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.status_code = status_code


def summarize_meeting(meeting, previous, user) -> dict:
    """
    1on1 の要約を作る。上司メモ（manager_private_notes）は共有される要約に混ざらないよう送らない。
    """
    client = get_client(user)
    if client is None:
        raise AISummaryError('AI機能が設定されていません（APIキーが未設定）', 503)
    if not (meeting.agenda.strip() or meeting.shared_notes.strip()):
        raise AISummaryError('アジェンダか共有メモを入力してから要約してください', 400)

    previous_items = '\n'.join(
        f'- [{"済" if i.get("done") else "未"}] ({"上司" if i.get("owner") == "manager" else "部下"}) {i.get("text", "")}'
        for i in (previous.action_items if previous else [])
    ) or '（なし）'

    content = f"""上司: {meeting.manager.full_name}
部下: {meeting.member.full_name}
実施日: {meeting.scheduled_at:%Y-%m-%d}

<agenda>
{meeting.agenda or '（なし）'}
</agenda>

<shared_notes>
{meeting.shared_notes or '（なし）'}
</shared_notes>

<previous_action_items>
{previous_items}
</previous_action_items>"""

    try:
        raw = client.with_options(timeout=120.0).messages.with_raw_response.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': content}],
            extra_headers={'anthropic-beta': 'server-side-fallback-2026-07-01'},
            extra_body={
                'fallbacks': 'default',
                'output_config': {
                    'effort': 'low',
                    'format': {'type': 'json_schema', 'schema': SUMMARY_SCHEMA},
                },
            },
        )
        body = raw.http_response.json()
    except anthropic.RateLimitError:
        raise AISummaryError('AI の利用が混み合っています。しばらくしてから再度お試しください', 429)
    except anthropic.APIStatusError as e:
        raise AISummaryError(f'AI生成に失敗しました: {e.message}', 502)
    except anthropic.APIConnectionError:
        raise AISummaryError('AI サービスに接続できませんでした', 502)

    if body.get('stop_reason') == 'refusal':
        raise AISummaryError('この内容は AI で要約できませんでした', 422)

    text = ''.join(b.get('text', '') for b in body.get('content', []) if b.get('type') == 'text')
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        raise AISummaryError('AI の応答を読み取れませんでした', 502)
    return {
        'summary':      result.get('summary', ''),
        'action_items': [{'text': i['text'], 'owner': i['owner'], 'done': False}
                         for i in result.get('action_items', []) if i.get('text')],
        'next_agenda':  [a for a in result.get('next_agenda', []) if a],
    }
