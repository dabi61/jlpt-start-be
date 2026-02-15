from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.cache import cache
from django.db import IntegrityError
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from .models import User
from .serializers import UserSerializer, UserProfileUpdateSerializer, AvatarConfirmSerializer
from .utils import generate_otp, send_otp_email
from .r2_storage import (
    R2StorageError,
    R2StorageConfigError,
    R2ObjectNotFoundError,
    R2StorageBadRequestError,
    create_avatar_upload,
    delete_avatar,
    head_avatar,
    is_configured,
    looks_like_avatar_key,
    public_url,
    upload_avatar_file,
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
    Create a one-time presigned upload URL for avatar upload (Cloudflare R2).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not is_configured():
            return Response(
                {'message': 'R2 storage is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            content_type = request.data.get('content_type') or request.data.get('contentType')
            filename = request.data.get('filename') or request.data.get('file_name')
            payload = create_avatar_upload(
                user_id=str(request.user.id),
                content_type=content_type,
                filename=filename,
            )
        except R2StorageConfigError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except R2StorageError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(payload, status=status.HTTP_200_OK)


class UserAvatarConfirmView(APIView):
    """
    Confirm uploaded object and set it as current user's avatar.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=AvatarConfirmSerializer,
        responses={200: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = AvatarConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image_id = serializer.validated_data['image_id']  # R2 object key

        if not is_configured():
            return Response(
                {'message': 'R2 storage is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            head = head_avatar(key=image_id, user_id=str(request.user.id))
            max_bytes = int(getattr(settings, 'R2_MAX_UPLOAD_BYTES', 0) or 0)
            if max_bytes and int(head.get('ContentLength') or 0) > max_bytes:
                # Best-effort cleanup.
                try:
                    delete_avatar(key=image_id, user_id=str(request.user.id))
                except R2StorageError:
                    pass
                return Response(
                    {'message': 'Image is too large.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            avatar_url = public_url(image_id)
        except R2ObjectNotFoundError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except R2StorageBadRequestError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except R2StorageConfigError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except R2StorageError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        user = request.user
        old_image_id = user.avatar_image_id
        user.avatar_image_id = image_id
        user.avatar = avatar_url
        user.save(update_fields=['avatar_image_id', 'avatar'])

        if old_image_id and old_image_id != image_id and looks_like_avatar_key(old_image_id):
            try:
                delete_avatar(key=old_image_id, user_id=str(request.user.id))
            except R2StorageError:
                # Non-blocking cleanup failure; keep new avatar.
                pass

        return Response(
            {
                'avatar': user.avatar,
                'avatar_image_id': user.avatar_image_id,
            },
            status=status.HTTP_200_OK,
        )


class UserAvatarView(APIView):
    """
    Update or delete current avatar stored in R2.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        """
        Upload avatar via backend and set it for the current user.

        Request:
          - multipart/form-data with field `file` (or `avatar` for backward compatibility), OR
          - raw bytes with `Content-Type: image/*` (optionally provide filename via `X-Filename`
            header or `?filename=...` query param)
        """
        if not is_configured():
            return Response(
                {'message': 'R2 storage is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        max_bytes = int(getattr(settings, 'R2_MAX_UPLOAD_BYTES', 0) or 0)
        raw_content_type = (getattr(request, 'content_type', '') or '').split(';', 1)[0].strip()

        # Avoid triggering DRF parsers for non-multipart requests.
        if raw_content_type.lower().startswith('multipart/form-data'):
            upload = request.FILES.get('file') or request.FILES.get('avatar')
            if not upload:
                return Response(
                    {'message': 'file is required.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if max_bytes and int(getattr(upload, 'size', 0) or 0) > max_bytes:
                return Response(
                    {'message': 'Image is too large.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            fileobj = getattr(upload, 'file', upload)
            content_type = getattr(upload, 'content_type', None) or None
            filename = getattr(upload, 'name', None) or None
        else:
            body = getattr(request, 'body', b'') or b''
            if not body:
                return Response(
                    {'message': 'file is required.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if max_bytes and len(body) > max_bytes:
                return Response(
                    {'message': 'Image is too large.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Accept only image uploads for the raw-bytes mode.
            raw_ct_lower = (raw_content_type or '').lower()
            if raw_ct_lower and not (
                raw_ct_lower.startswith('image/') or raw_ct_lower in ('application/octet-stream', 'binary/octet-stream')
            ):
                return Response(
                    {'message': 'Unsupported content type.'},
                    status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            fileobj = body
            content_type = raw_content_type or None
            filename = request.headers.get('X-Filename') or request.query_params.get('filename') or None

        try:
            result = upload_avatar_file(
                user_id=str(request.user.id),
                fileobj=fileobj,
                content_type=content_type,
                filename=filename,
            )
        except R2StorageBadRequestError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except R2StorageConfigError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except R2StorageError as exc:
            return Response({'message': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        user = request.user
        old_image_id = user.avatar_image_id
        user.avatar_image_id = result['image_id']
        user.avatar = result['public_url']
        user.save(update_fields=['avatar_image_id', 'avatar'])

        if old_image_id and old_image_id != user.avatar_image_id and looks_like_avatar_key(old_image_id):
            try:
                delete_avatar(key=old_image_id, user_id=str(request.user.id))
            except R2StorageError:
                # Non-blocking cleanup failure; keep new avatar.
                pass

        return Response(
            {
                'avatar': user.avatar,
                'avatar_image_id': user.avatar_image_id,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        # Some clients struggle with multipart PUT; allow POST as an alias.
        return self.put(request)

    def delete(self, request):
        user = request.user
        image_id = (user.avatar_image_id or '').strip()

        if image_id and looks_like_avatar_key(image_id):
            if not is_configured():
                return Response(
                    {'message': 'R2 storage is not configured.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            try:
                delete_avatar(key=image_id, user_id=str(request.user.id))
            except R2StorageBadRequestError:
                # Ignore invalid historical keys; still clear profile fields.
                pass
            except R2StorageError as exc:
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
