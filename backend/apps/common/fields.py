"""
暗号化して DB に保存するフィールド

- 保存時に Fernet（AES-128-CBC + HMAC-SHA256）で暗号化し、"enc:" を付けて保存する
- 読み込み時に復号する。"enc:" のない値は移行前の平文としてそのまま返す
- 鍵は settings.FIELD_ENCRYPTION_KEY（未設定なら SECRET_KEY から導出。開発用）
"""
import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

PREFIX = 'enc:'


@lru_cache(maxsize=4)
def _fernet(key: str) -> Fernet:
    if key:
        return Fernet(key.encode())
    derived = hashlib.sha256(('hrm-field-encryption:' + settings.SECRET_KEY).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def get_fernet() -> Fernet:
    return _fernet(getattr(settings, 'FIELD_ENCRYPTION_KEY', '') or '')


def encrypt_value(value: str) -> str:
    if value in (None, '') or str(value).startswith(PREFIX):
        return value
    return PREFIX + get_fernet().encrypt(str(value).encode()).decode()


def decrypt_value(value: str) -> str:
    if not value or not str(value).startswith(PREFIX):
        return value
    try:
        return get_fernet().decrypt(value[len(PREFIX):].encode()).decode()
    except InvalidToken:
        # 鍵が違う・壊れている場合は空として扱う（暗号文を外に出さない）
        return ''


class EncryptedTextField(models.TextField):
    """暗号化して保存する文字列フィールド。検索・並び替えには使えない"""

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        return decrypt_value(super().to_python(value))

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)
