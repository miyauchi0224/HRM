"""
初期パスワードの発行

社員登録（画面・CSV一括登録・サンプルデータ投入）で作るアカウントの初期パスワードは
生年月日の 8 桁（YYYYMMDD）とする。推測されやすいため、アカウントには
must_change_password=True を立て、初回ログイン時にパスワード変更を求める。
生年月日が未登録の場合はランダムな文字列を発行する。
"""
import secrets
from datetime import date


def initial_password_for(birth_date: date | None) -> str:
    if birth_date:
        return birth_date.strftime('%Y%m%d')
    return secrets.token_urlsafe(12)
