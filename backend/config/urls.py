from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/',        include('apps.accounts.urls')),
    path('api/v1/employees/',   include('apps.employees.urls')),
    path('api/v1/attendance/',  include('apps.attendance.urls')),
    path('api/v1/leave/',       include('apps.leave.urls')),
    path('api/v1/mbo/',         include('apps.mbo.urls')),
    path('api/v1/salary/',      include('apps.salary.urls')),
    path('api/v1/expense/',     include('apps.expense.urls')),
    path('api/v1/skills/',      include('apps.skills.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/todo/',          include('apps.todo.urls')),
    path('api/v1/intra/',         include('apps.intra.urls')),
    # API ドキュメント
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ヘルスチェック（App Runnerが死活確認に使う）
    path('api/v1/health/', lambda r: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'status': 'ok'})),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
