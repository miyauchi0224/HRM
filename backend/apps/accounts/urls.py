from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('login/',            views.LoginView.as_view(),          name='auth-login'),
    path('logout/',           views.logout_view,                  name='auth-logout'),
    path('refresh/',          TokenRefreshView.as_view(),         name='auth-refresh'),
    path('me/',               views.me_view,                      name='auth-me'),
    path('password/change/',  views.change_password_view,         name='auth-password-change'),
]
