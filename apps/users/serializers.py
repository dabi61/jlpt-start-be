"""
Serializers for User model.
"""
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'display_name',
            'avatar',
            'first_name',
            'last_name',
            'role',
            'login_method',
            'status',
            'level',
            'streak',
            'last_study_date',
            'date_joined',
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'role', 'login_method', 'status']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['display_name', 'avatar', 'first_name', 'last_name', 'level']


class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer that removes username and adds display_name."""

    username = None
    display_name = serializers.CharField(required=False, allow_blank=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['display_name'] = self.validated_data.get('display_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.display_name = self.cleaned_data.get('display_name', '')
        # Set status to inactive until verified
        user.status = User.Status.INACTIVE
        user.save()

        # Generate and send OTP
        from .utils import generate_otp, send_otp_email
        otp = generate_otp(user.email)
        send_otp_email(user.email, otp)

        return user
        return user


from dj_rest_auth.serializers import LoginSerializer

class CustomLoginSerializer(LoginSerializer):
    """
    Custom Login Serializer to remove username field entirely.
    """
    username = None
