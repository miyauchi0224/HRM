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
    path('api/v1/approval/',      include('apps.approval.urls')),
    path('api/v1/chat/',          include('apps.chat.urls')),
    path('api/v1/recruitment/',   include('apps.recruitment.urls')),
    path('api/v1/assets/',        include('apps.assets.urls')),
    path('api/v1/evaluation/',    include('apps.evaluation.urls')),
    path('api/v1/learning/',      include('apps.learning.urls')),
    path('api/v1/analytics/',     include('apps.analytics.urls')),
    path('api/v1/ai/',            include('apps.ai_assistant.urls')),
    path('api/v1/onboarding/',    include('apps.onboarding.urls')),
    path('api/v1/documents/',     include('apps.documents.urls')),
    path('api/v1/stress-check/',  include('apps.stress_check.urls')),
    path('api/v1/calendar/',      include('apps.calendar_sync.urls')),
    path('api/v1/compliance/',    include('apps.compliance.urls')),
    # API ドキュメント
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',   SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # ヘルスチェック（App Runnerが死活確認に使う）
    path('api/v1/health/', lambda r: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'status': 'ok'})),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
