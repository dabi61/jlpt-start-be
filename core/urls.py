"""
URL configuration for Nihongo Project.
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from apps.users.views import CustomRegisterView, CustomLoginView, CustomTokenRefreshView
from dj_rest_auth.views import PasswordResetConfirmView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication (dj-rest-auth)
    # Override login/register/refresh views to use custom ones (public access/custom structure)
    path('api/auth/login/', CustomLoginView.as_view(), name='custom_login'),
    path('api/auth/registration/', CustomRegisterView.as_view(), name='custom_registration'),
    path('api/auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    # Fix for Password Reset: dj-rest-auth needs this specific name to generate email links
    path('api/auth/password/reset/confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    # Include other auth urls
    path('api/auth/', include('dj_rest_auth.urls')),
    # path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # App URLs (priority order)
    path('api/users/', include('apps.users.urls')),
    path('api/n4/', include('apps.n4.urls')),
    path('api/n5/', include('apps.n5.urls')),
    path('api/vocabulary/', include('apps.vocabulary.urls')),
    path('api/kanjis/', include('apps.kanjis.urls')),
    path('api/grammar/', include('apps.grammar.urls')),
    path('api/examples/', include('apps.examples.urls')),
    # Remaining APIs
    path('api/learning/', include('apps.learning.urls')),
    path('api/courses/', include('apps.courses.urls')),
]
