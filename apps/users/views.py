from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import User
from .serializers import UserSerializer, UserProfileUpdateSerializer, AvatarConfirmSerializer
from .utils import generate_otp, send_otp_email
from .cloudflare_images import (
    CloudflareImagesError,
    CloudflareImagesConfigError,
    create_direct_upload,
    delete_image,
    get_image,
    is_configured,
    resolve_avatar_url,
)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for retrieving and updating the current user's profile.

    GET: Retrieve current user profile
    PUT/PATCH: Update current user profile
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer


class UserStatsView(APIView):
    """
    API endpoint for retrieving current user's learning statistics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'level': user.level,
            'streak': user.streak,
            'last_study_date': user.last_study_date,
            'display_name': user.name,
        })


class UserAvatarUploadURLView(APIView):
    """
    Create a one-time Cloudflare direct upload URL for avatar upload.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not is_configured():
            return Response(
                {'message': 'Cloudflare Images is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            payload = create_direct_upload(user_id=str(request.user.id))
        except CloudflareImagesError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(payload, status=status.HTTP_200_OK)


class UserAvatarConfirmView(APIView):
    """
    Confirm uploaded image and set it as current user's avatar.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AvatarConfirmSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = AvatarConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_id = serializer.validated_data['image_id']

        if not is_configured():
            return Response(
                {'message': 'Cloudflare Images is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            image = get_image(image_id)
            if bool(image.get('draft')):
                return Response(
                    {'message': 'Image upload is not completed yet.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            avatar_url = resolve_avatar_url(image)
        except CloudflareImagesConfigError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except CloudflareImagesError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        user = request.user
        old_image_id = user.avatar_image_id
        user.avatar_image_id = image_id
        user.avatar = avatar_url
        user.save(update_fields=['avatar_image_id', 'avatar'])

        if old_image_id and old_image_id != image_id:
            try:
                delete_image(old_image_id)
            except CloudflareImagesError:
                # Non-blocking cleanup failure; keep new avatar.
                pass

        return Response(
            {
                'avatar': user.avatar,
                'avatar_image_id': user.avatar_image_id,
            },
            status=status.HTTP_200_OK,
        )


class UserAvatarDeleteView(APIView):
    """
    Delete current avatar from Cloudflare and clear profile avatar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        image_id = (user.avatar_image_id or '').strip()

        if image_id:
            if not is_configured():
                return Response(
                    {'message': 'Cloudflare Images is not configured.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            try:
                delete_image(image_id)
            except CloudflareImagesError as exc:
                return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        user.avatar = None
        user.avatar_image_id = None
        user.save(update_fields=['avatar', 'avatar_image_id'])

        return Response(
            {
                'avatar': user.avatar,
                'avatar_image_id': user.avatar_image_id,
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    API endpoint to verify OTP and activate user account.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'otp': {'type': 'string'}
                },
                'required': ['email', 'otp']
            }
        },
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')

        if not email or not otp:
            return Response({'message': 'Email and OTP are required'}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = cache.get(f"otp_{email}")

        if cached_otp and cached_otp == otp:
            try:
                user = User.objects.get(email=email)
                user.status = User.Status.ACTIVE
                user.is_active = True
                user.save()
                cache.delete(f"otp_{email}")
                return Response({'message': 'Account verified successfully'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'message': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)


class ResendOTPView(APIView):
    """
    API endpoint to resend OTP to user.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'}
                },
                'required': ['email']
            }
        },
        responses={200: OpenApiTypes.OBJECT}
    )
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'message': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            User.objects.get(email=email)
            otp = generate_otp(email)
            send_otp_email(email, otp)
            return Response({'message': 'OTP sent successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
from dj_rest_auth.registration.views import RegisterView
from dj_rest_auth.views import LoginView
from django.conf import settings

class CustomLoginView(LoginView):
    """
    Custom Login View to ensure authentication_classes are empty.
    This prevents errors if a client sends an invalid token to the login endpoint.
    """
    authentication_classes = []

    def get_response(self):
        original_response = super().get_response()
        data = original_response.data

        from rest_framework_simplejwt.tokens import RefreshToken
        from jwt import decode as jwt_decode

        # Ensure user is available
        user = self.user

        # 1. Handle Refresh Token Generation
        if 'refresh' not in data or not data['refresh']:
             refresh = RefreshToken.for_user(user)
             refresh_str = str(refresh)
        else:
            refresh_str = data['refresh']

        # 2. Extract Access Token
        access_str = data.get('access')

        # 3. Calculate Expirations
        access_exp = None
        refresh_exp = None

        try:
             if access_str:
                 decoded_access = jwt_decode(access_str, options={"verify_signature": False})
                 access_exp = decoded_access.get('exp')

             decoded_refresh = jwt_decode(refresh_str, options={"verify_signature": False})
             refresh_exp = decoded_refresh.get('exp')
        except Exception:
            pass

        # 4. Reconstruct Response Data
        new_data = {
            'user': data.get('user'),
            'access': {
                'token': access_str,
                'expires_at': access_exp
            },
            'refresh': {
                'token': refresh_str,
                'expires_at': refresh_exp
            }
        }

        original_response.data = new_data
        return original_response


from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.settings import api_settings

class CustomTokenRefreshView(TokenRefreshView):
    """
    Custom Refresh View to return tokens in the same structured format:
    {
      "access": { "token": ..., "expires_at": ... },
      "refresh": { "token": ..., "expires_at": ... }
    }
    """
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        data = response.data

        # SimpleJWT Refresh view returns 'access' and optionally 'refresh' (if rotation on)
        access_str = data.get('access')
        refresh_str = data.get('refresh')

        from jwt import decode as jwt_decode
        access_exp = None
        refresh_exp = None

        try:
             if access_str:
                 decoded_access = jwt_decode(access_str, options={"verify_signature": False})
                 access_exp = decoded_access.get('exp')

             if refresh_str:
                 decoded_refresh = jwt_decode(refresh_str, options={"verify_signature": False})
                 refresh_exp = decoded_refresh.get('exp')
        except Exception:
            pass

        new_data = {
            'access': {
                'token': access_str,
                'expires_at': access_exp
            }
        }

        if refresh_str:
            new_data['refresh'] = {
                'token': refresh_str,
                'expires_at': refresh_exp
            }

        response.data = new_data
        return response

class CustomRegisterView(RegisterView):
    """
    Custom Register View to prevent auto-login and returning token/user info.
    Instead, it returns a success message prompting OTP verification.
    """
    authentication_classes = [] # Explicitly ignore any auth headers (tokens) sent by client

    def create(self, request, *args, **kwargs):
        # Manually handle registration to avoid dj-rest-auth's auto-login logic
        # which fails because our user is initially INACTIVE
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save the user (this triggers CustomRegisterSerializer.save which sends OTP)
        # Guard race-condition where duplicate email can still happen between
        # validation and insert.
        try:
            user = serializer.save(request)
        except IntegrityError:
            return Response(
                {
                    "message": "A user is already registered with this e-mail address.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        email = request.data.get('email')
        return Response(
            {
                "message": "Verification Code has been sent to your email.",
                "email": email,
            },
            status=status.HTTP_201_CREATED
        )
