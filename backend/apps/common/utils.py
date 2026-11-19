"""
共通ユーティリティ

複数アプリで使う小さな関数をまとめる。
"""
from datetime import date


def fiscal_year_of(d: date) -> int:
    """日付が属する年度（4月始まり）を返す。2026-03-31 → 2025, 2026-04-01 → 2026"""
    return d.year if d.month >= 4 else d.year - 1


def get_client_ip(request):
    """リクエスト元の IP アドレス（X-Forwarded-For の先頭を優先）"""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR') or None


def users_with_roles(*roles):
    """指定ロールのいずれかを持つ有効なユーザー一覧（roles は JSON 配列のため Python 側で絞り込む）"""
    from apps.accounts.models import User
    return [u for u in User.objects.filter(is_active=True) if any(r in (u.roles or []) for r in roles)]
