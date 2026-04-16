"""
PDF フォント登録モジュール。
Django 起動時（AppConfig.ready）に一度だけ呼び出す。
reportlab の UnicodeCIDFont 初期化は重いため、リクエストごとに実行せずここで事前登録する。
"""
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

_registered = False


def register_fonts():
    """日本語フォントを一度だけ登録する（冪等）"""
    global _registered
    if _registered:
        return
    try:
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
        pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
        _registered = True
    except Exception:
        # フォントが利用不可の環境ではスキップ（テスト環境など）
        pass
