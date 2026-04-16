import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

# PDF フォントをサーバー起動時に一度だけ登録（リクエストごとの初期化コストを排除）
from config.pdf_fonts import register_fonts
register_fonts()
