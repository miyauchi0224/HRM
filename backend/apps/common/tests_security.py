"""
common/tests_security.py
========================
インジェクション対策（HTML 無害化・アップロード検証・CSV/Excel 数式対策・メディア配信ヘッダー）のテスト。
"""
import csv
import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.exceptions import ValidationError

from apps.common.security import (
    sanitize_html, validate_upload, safe_filename, neutralize_cell,
    safe_csv_writer, set_xlsx_value, IMAGE_EXTENSIONS,
)
from conftest import ApprovalRequestFactory


def png_bytes():
    buf = io.BytesIO()
    Image.new('RGB', (2, 2), 'red').save(buf, format='PNG')
    return buf.getvalue()


@pytest.fixture
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


# ─────────────────────────────────────────────────────────────────────────────
# ▌ HTML の無害化
# ─────────────────────────────────────────────────────────────────────────────

class TestSanitizeHtml:
    @pytest.mark.parametrize('payload', [
        '<script>alert(1)</script>',
        '<img src=x onerror="alert(1)">',
        '<a href="javascript:alert(1)">x</a>',
        '<a href="JaVaScRiPt:alert(1)">x</a>',
        '<svg onload="alert(1)"></svg>',
        '<iframe src="https://evil.example"></iframe>',
        '<p style="background:url(javascript:alert(1))">x</p>',
        '<div onclick="alert(1)">x</div>',
        '<img src="data:text/html;base64,PHNjcmlwdD4=">',
    ])
    def test_dangerous_markup_removed(self, payload):
        out = sanitize_html(payload).lower()
        assert '<script' not in out
        assert 'onerror' not in out and 'onload' not in out and 'onclick' not in out
        assert 'javascript:' not in out
        assert '<iframe' not in out and '<svg' not in out
        assert 'data:' not in out

    def test_safe_markup_kept(self):
        html = ('<h2>見出し</h2><p style="text-align: center">本文<strong>太字</strong></p>'
                '<a href="https://example.com" target="_blank">link</a><img src="/media/intra/a.png" alt="a">'
                '<table><tr><td colspan="2">x</td></tr></table>')
        out = sanitize_html(html)
        assert '<h2>見出し</h2>' in out
        assert 'text-align' in out
        assert 'href="https://example.com"' in out
        assert 'rel="noopener noreferrer"' in out
        assert 'src="/media/intra/a.png"' in out
        assert 'colspan="2"' in out


@pytest.mark.django_db
class TestArticleSanitizeApi:
    BASE = '/api/v1/intra/articles/'

    def test_html_article_sanitized_on_create(self, auth_client):
        res = auth_client.post(self.BASE, {
            'title': 't', 'category': 'announcement', 'format': 'html',
            'content': '<p>ok</p><img src=x onerror=alert(1)><script>alert(1)</script>',
        }, format='json')
        assert res.status_code == 201, res.data
        from apps.intra.models import Article
        content = Article.objects.get(id=res.data['id']).content
        assert 'onerror' not in content and '<script' not in content
        assert '<p>ok</p>' in content

    def test_switching_to_html_sanitizes_existing_content(self, auth_client):
        res = auth_client.post(self.BASE, {
            'title': 't', 'category': 'announcement', 'format': 'text',
            'content': '<img src=x onerror=alert(1)>',
        }, format='json')
        assert res.status_code == 201, res.data
        res = auth_client.patch(f"{self.BASE}{res.data['id']}/", {'format': 'html'}, format='json')
        assert res.status_code == 200, res.data
        from apps.intra.models import Article
        assert 'onerror' not in Article.objects.get(id=res.data['id']).content

    def test_markdown_content_kept_as_is(self, auth_client):
        """Markdown は保存時に変更しない（表示側の react-markdown が HTML を描画しない）"""
        res = auth_client.post(self.BASE, {
            'title': 't', 'category': 'announcement', 'format': 'markdown', 'content': '# a\n<b>x</b>',
        }, format='json')
        assert res.status_code == 201, res.data
        from apps.intra.models import Article
        assert Article.objects.get(id=res.data['id']).content == '# a\n<b>x</b>'


# ─────────────────────────────────────────────────────────────────────────────
# ▌ アップロード検証
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateUpload:
    @pytest.mark.parametrize('name', ['evil.html', 'evil.htm', 'evil.svg', 'evil.js', 'evil.exe', 'noext'])
    def test_disallowed_extensions_rejected(self, name):
        f = SimpleUploadedFile(name, b'<script>alert(1)</script>', content_type='image/png')
        with pytest.raises(ValidationError):
            validate_upload(f)

    def test_fake_image_rejected(self):
        f = SimpleUploadedFile('a.png', b'<html><script>alert(1)</script></html>', content_type='image/png')
        with pytest.raises(ValidationError):
            validate_upload(f, allowed=IMAGE_EXTENSIONS)

    def test_extension_content_mismatch_rejected(self):
        f = SimpleUploadedFile('a.jpg', png_bytes(), content_type='image/jpeg')
        with pytest.raises(ValidationError):
            validate_upload(f, allowed=IMAGE_EXTENSIONS)

    def test_content_type_decided_by_server(self):
        f = SimpleUploadedFile('report.pdf', b'%PDF-1.4', content_type='text/html')
        assert validate_upload(f) == 'application/pdf'

    def test_real_image_accepted(self):
        f = SimpleUploadedFile('a.png', png_bytes(), content_type='application/octet-stream')
        assert validate_upload(f, allowed=IMAGE_EXTENSIONS) == 'image/png'
        assert f.tell() == 0

    def test_size_limit(self):
        f = SimpleUploadedFile('a.pdf', b'x' * 2048)
        with pytest.raises(ValidationError):
            validate_upload(f, max_size=1024)

    @pytest.mark.parametrize('name,expected', [
        ('../../etc/passwd.pdf', 'passwd.pdf'),
        ('a"\r\nX-Evil: 1.pdf', 'aX-Evil 1.pdf'),
        ('C:\\Users\\x\\file.pdf', 'file.pdf'),
        ('', 'file'),
    ])
    def test_safe_filename(self, name, expected):
        assert safe_filename(name) == expected


@pytest.mark.django_db
class TestUploadApi:
    def test_approval_rejects_html_attachment(self, auth_client, employee_user, media_tmp):
        req = ApprovalRequestFactory(applicant=employee_user)
        f = SimpleUploadedFile('x.html', b'<script>alert(1)</script>', content_type='application/pdf')
        res = auth_client.post(f'/api/v1/approval/requests/{req.id}/attachments/', {'file': f}, format='multipart')
        assert res.status_code == 400

    def test_approval_download_is_attachment_with_server_type(self, auth_client, employee_user, media_tmp):
        req = ApprovalRequestFactory(applicant=employee_user)
        f = SimpleUploadedFile('見積"書.pdf', b'%PDF-1.4 test', content_type='text/html')
        res = auth_client.post(f'/api/v1/approval/requests/{req.id}/attachments/', {'file': f}, format='multipart')
        assert res.status_code == 201, res.data
        assert res.data['content_type'] == 'application/pdf'

        res = auth_client.get(f"/api/v1/approval/requests/{req.id}/attachments/{res.data['id']}/download/")
        assert res.status_code == 200
        assert res['Content-Type'] == 'application/pdf'
        assert res['Content-Disposition'].startswith('attachment;')
        assert res['X-Content-Type-Options'] == 'nosniff'

    def test_intra_rejects_svg(self, auth_client, media_tmp):
        f = SimpleUploadedFile('x.svg', b'<svg onload="alert(1)"/>', content_type='image/svg+xml')
        res = auth_client.post('/api/v1/intra/upload/', {'image': f}, format='multipart')
        assert res.status_code == 400

    def test_intra_rejects_fake_png(self, auth_client, media_tmp):
        f = SimpleUploadedFile('x.png', b'<script>alert(1)</script>', content_type='image/png')
        res = auth_client.post('/api/v1/intra/upload/', {'image': f}, format='multipart')
        assert res.status_code == 400

    def test_intra_accepts_png(self, auth_client, media_tmp):
        f = SimpleUploadedFile('x.png', png_bytes(), content_type='image/png')
        res = auth_client.post('/api/v1/intra/upload/', {'image': f}, format='multipart')
        assert res.status_code == 201


# ─────────────────────────────────────────────────────────────────────────────
# ▌ メディア配信ヘッダー
# ─────────────────────────────────────────────────────────────────────────────

class TestMediaHeaders:
    def test_html_in_media_is_sandboxed_and_downloaded(self):
        from apps.common.middleware import MediaSecurityHeadersMiddleware
        from django.http import HttpResponse
        from django.test import RequestFactory
        mw = MediaSecurityHeadersMiddleware(lambda r: HttpResponse('<script>alert(1)</script>', content_type='text/html'))
        res = mw(RequestFactory().get('/media/chat/attachments/evil.html'))
        assert 'sandbox' in res['Content-Security-Policy']
        assert res['Content-Disposition'] == 'attachment'
        assert res['X-Content-Type-Options'] == 'nosniff'

    def test_image_in_media_is_inline(self):
        from apps.common.middleware import MediaSecurityHeadersMiddleware
        from django.http import HttpResponse
        from django.test import RequestFactory
        mw = MediaSecurityHeadersMiddleware(lambda r: HttpResponse(b'', content_type='image/png'))
        res = mw(RequestFactory().get('/media/avatars/a.png'))
        assert 'sandbox' in res['Content-Security-Policy']
        assert 'Content-Disposition' not in res

    def test_non_media_path_untouched(self):
        from apps.common.middleware import MediaSecurityHeadersMiddleware
        from django.http import HttpResponse
        from django.test import RequestFactory
        mw = MediaSecurityHeadersMiddleware(lambda r: HttpResponse('ok'))
        res = mw(RequestFactory().get('/api/v1/health/'))
        assert 'Content-Security-Policy' not in res


# ─────────────────────────────────────────────────────────────────────────────
# ▌ CSV / Excel 数式インジェクション
# ─────────────────────────────────────────────────────────────────────────────

class TestFormulaInjection:
    @pytest.mark.parametrize('value,expected', [
        ('=HYPERLINK("http://evil","x")', '\'=HYPERLINK("http://evil","x")'),
        ('+cmd|\' /C calc\'!A0', '\'+cmd|\' /C calc\'!A0'),
        ('-2+3', "'-2+3"),
        ('@SUM(A1)', "'@SUM(A1)"),
        ('\t=1', "'\t=1"),
        ('-5', '-5'),
        ('+1.5', '+1.5'),
        ('-1,000', '-1,000'),
        ('山田', '山田'),
        ('090-1234-5678', '090-1234-5678'),
        (-5, -5),
        (None, None),
    ])
    def test_neutralize_cell(self, value, expected):
        assert neutralize_cell(value) == expected

    def test_safe_csv_writer(self):
        buf = io.StringIO()
        w = safe_csv_writer(buf)
        w.writerow(['=1+1', 'ok', 3])
        w.writerows([['@x'], ['y']])
        rows = list(csv.reader(io.StringIO(buf.getvalue())))
        assert rows == [["'=1+1", 'ok', '3'], ["'@x"], ['y']]

    def test_set_xlsx_value_keeps_formula_as_text(self):
        ws = openpyxl.Workbook().active
        c = set_xlsx_value(ws.cell(row=1, column=1), '=HYPERLINK("http://evil","x")')
        assert c.data_type == 's'
        c2 = ws.cell(row=2, column=1, value='=1+1')
        assert c2.data_type == 'f'  # 対策なしの場合は数式になる（比較用）
        assert set_xlsx_value(ws.cell(row=3, column=1), 100).value == 100
