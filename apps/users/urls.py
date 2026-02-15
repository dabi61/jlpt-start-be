"""
URL patterns for User API.
"""
from django.urls import path

from .views import (
    UserProfileView,
    UserStatsView,
    UserAvatarUploadURLView,
    UserAvatarConfirmView,
    UserAvatarView,
    VerifyOTPView,
    ResendOTPView
)

app_name = 'users'

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('avatar/upload-url/', UserAvatarUploadURLView.as_view(), name='avatar-upload-url'),
    path('avatar/confirm/', UserAvatarConfirmView.as_view(), name='avatar-confirm'),
    path('avatar/', UserAvatarView.as_view(), name='avatar-delete'),
    path('stats/', UserStatsView.as_view(), name='stats'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
]
