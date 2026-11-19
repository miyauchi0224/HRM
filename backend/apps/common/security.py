"""
インジェクション対策の共通処理

- sanitize_html      : 利用者が書いた HTML から script・イベント属性・javascript: URL などを除去
- validate_upload    : アップロードファイルの拡張子・サイズ・中身（画像）を検証し、
                       サーバー側で決めた Content-Type を返す
- attachment_response: ダウンロード用レスポンス（必ず attachment・ファイル名は安全にエンコード）
- safe_csv_writer / neutralize_cell / set_xlsx_value:
                       CSV / Excel に書き出す値が数式として実行されないようにする
"""
import csv
import mimetypes
import os
import re
import unicodedata

import nh3
from django.http import FileResponse
from rest_framework.exceptions import ValidationError

# ── HTML の無害化 ────────────────────────────────────────────────

ALLOWED_HTML_TAGS = {
    'a', 'abbr', 'b', 'blockquote', 'br', 'caption', 'code', 'col', 'colgroup',
    'dd', 'del', 'div', 'dl', 'dt', 'em', 'figcaption', 'figure',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'ins', 'kbd',
    'li', 'mark', 'ol', 'p', 'pre', 's', 'small', 'span', 'strong', 'sub', 'sup',
    'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul',
}
ALLOWED_HTML_ATTRIBUTES = {
    '*':   {'class', 'style', 'title'},
    'a':   {'href', 'target'},
    'img': {'src', 'alt', 'width', 'height'},
    'td':  {'colspan', 'rowspan', 'align'},
    'th':  {'colspan', 'rowspan', 'align', 'scope'},
    'col': {'span'},
    'ol':  {'start'},
}
# style 属性で許可する CSS プロパティ（url() などは使えない）
ALLOWED_STYLE_PROPERTIES = {
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'width', 'height', 'max-width',
    'margin', 'margin-left', 'margin-right', 'padding', 'border', 'vertical-align',
}
ALLOWED_URL_SCHEMES = {'http', 'https', 'mailto'}


def sanitize_html(html: str) -> str:
    """利用者が入力した HTML を許可リスト方式で無害化する"""
    if not html:
        return html
    return nh3.clean(
        html,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        filter_style_properties=ALLOWED_STYLE_PROPERTIES,
        link_rel='noopener noreferrer',
    )


# ── アップロードの検証 ───────────────────────────────────────────

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
DOCUMENT_EXTENSIONS = {
    '.pdf', '.txt', '.csv', '.md',
    '.doc', '.docx', '.xls', '.xlsx', '.xlsm', '.ppt', '.pptx',
    '.odt', '.ods', '.odp', '.rtf', '.zip',
}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm', '.mp3', '.m4a'}
ATTACHMENT_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | {'.heic'}

# 拡張子 → サーバー側で決める Content-Type（ブラウザの申告は使わない）
_CONTENT_TYPES = {
    '.md':   'text/markdown',
    '.csv':  'text/csv',
    '.txt':  'text/plain',
    '.heic': 'image/heic',
    '.webp': 'image/webp',
    '.xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12',
    '.m4a':  'audio/mp4',
}
_PIL_FORMATS = {
    '.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.gif': 'GIF', '.webp': 'WEBP',
}


def content_type_for(filename: str) -> str:
    ext = os.path.splitext(filename or '')[1].lower()
    return (
        _CONTENT_TYPES.get(ext)
        or mimetypes.guess_type('x' + ext)[0]
        or 'application/octet-stream'
    )


def safe_filename(name: str, max_length: int = 200) -> str:
    """パス区切り・制御文字・引用符を除いた表示用ファイル名"""
    name = os.path.basename((name or '').replace('\\', '/'))
    name = ''.join(
        ch for ch in name
        if unicodedata.category(ch)[0] != 'C' and ch not in '"<>|:*?'
    ).strip(' .')
    if not name:
        name = 'file'
    if len(name) > max_length:
        base, ext = os.path.splitext(name)
        name = base[: max_length - len(ext)] + ext
    return name


def validate_upload(file, allowed=ATTACHMENT_EXTENSIONS, max_size=None) -> str:
    """
    拡張子の許可リスト・サイズ・画像の中身を検証する。
    問題があれば ValidationError（400）。正常ならサーバー側で決めた Content-Type を返す。
    """
    ext = os.path.splitext(file.name or '')[1].lower()
    if ext not in allowed:
        raise ValidationError({'file': f'この形式のファイルはアップロードできません（{ext or "拡張子なし"}）'})
    if max_size is not None and file.size > max_size:
        raise ValidationError({'file': f'ファイルサイズは {max_size // (1024 * 1024)}MB 以内にしてください'})

    pil_format = _PIL_FORMATS.get(ext)
    if pil_format:
        from PIL import Image, UnidentifiedImageError
        try:
            file.seek(0)
            with Image.open(file) as img:
                actual = img.format
                img.verify()
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
            raise ValidationError({'file': '画像ファイルとして読み込めません'})
        finally:
            file.seek(0)
        if actual != pil_format and not (pil_format == 'JPEG' and actual == 'MPO'):
            raise ValidationError({'file': '拡張子とファイルの中身が一致しません'})

    return content_type_for(file.name)


def attachment_response(fileobj, filename: str) -> FileResponse:
    """
    ダウンロード用レスポンス。保存済みの Content-Type は信用せず拡張子から決め、
    常に attachment で返す（ファイル名は Django が RFC 6266 形式でエンコード）。
    """
    name = safe_filename(filename)
    return FileResponse(
        fileobj,
        as_attachment=True,
        filename=name,
        content_type=content_type_for(name),
    )


# ── CSV / Excel の数式インジェクション対策 ──────────────────────

_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r', '\n')
_NUMBER_RE = re.compile(r'^[+-]?(\d[\d,]*(\.\d+)?|\.\d+)$')


def neutralize_cell(value):
    """
    表計算ソフトで数式として解釈される文字列の先頭に ' を付ける。
    数値型や「-5」「+1.5」のような数値表現の文字列はそのまま。
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES) and not _NUMBER_RE.match(value):
        return "'" + value
    return value


class SafeCSVWriter:
    """csv.writer と同じ使い方で、各セルに neutralize_cell を適用する"""

    def __init__(self, f, *args, **kwargs):
        self._writer = csv.writer(f, *args, **kwargs)

    def writerow(self, row):
        return self._writer.writerow([neutralize_cell(v) for v in row])

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


def safe_csv_writer(f, *args, **kwargs) -> SafeCSVWriter:
    return SafeCSVWriter(f, *args, **kwargs)


def set_xlsx_value(cell, value):
    """openpyxl のセルに値を入れる。'=' で始まる文字列も数式ではなく文字列として保存する"""
    cell.value = value
    if isinstance(value, str) and value.startswith('='):
        cell.data_type = 's'
    return cell
