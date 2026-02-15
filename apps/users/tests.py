from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import MagicMock, patch

User = get_user_model()

class AuthFlowTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('custom_registration')  # Our custom registration endpoint
        self.verify_otp_url = reverse('users:verify-otp')
        self.login_url = '/api/auth/login/'  # dj-rest-auth default
        self.change_password_url = '/api/auth/password/change/'

        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',  # dj-rest-auth might require this depending on config, usually password1/password is enough or configured fields
            'display_name': 'Test User'
        }
        # Adjusting data keys to match ACCOUNT_SIGNUP_FIELDS = ['email', 'password1', 'password2']
        self.register_payload = {
            'email': 'testuser@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'display_name': 'Test User'
        }

    @staticmethod
    def _body(response):
        """Return rendered JSON payload as received by API clients."""
        return response.json()

    def test_full_auth_flow(self):
        """
        Test the complete flow: Register -> Verify OTP -> Login -> Change Password
        """
        # 1. Registration
        response = self.client.post(self.register_url, self.register_payload)
        response_body = self._body(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_body['meta']['code'], status.HTTP_201_CREATED)
        self.assertEqual(response_body['meta']['type'], 'SUCCESS')
        self.assertIn('Verification Code has been sent', response_body['meta']['message'])
        self.assertEqual(response_body['data']['email'], self.user_data['email'])
        self.assertNotIn('key', response_body['data'])  # Ensure no token is returned
        self.assertNotIn('access', response_body['data'])

        # Verify User is created but INACTIVE
        user = User.objects.get(email=self.user_data['email'])
        self.assertEqual(user.status, User.Status.INACTIVE)
        self.assertFalse(user.is_active)

        # 2. Login ATTEMPT (Should fail because inactive)
        login_payload = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        login_response = self.client.post(self.login_url, login_payload)
        # dj-rest-auth returns 400 or 403 for inactive users depending on config
        # Default AllAuth/dj-rest-auth might return 'E-mail is not verified.'
        self.assertNotEqual(login_response.status_code, status.HTTP_200_OK)

        # 3. OTP Verification
        # Retrieve OTP from Cache
        otp = cache.get(f"otp_{user.email}")
        self.assertIsNotNone(otp)

        verify_payload = {
            'email': user.email,
            'otp': otp
        }
        verify_response = self.client.post(self.verify_otp_url, verify_payload)
        verify_response_body = self._body(verify_response)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_response_body['meta']['message'], 'Account verified successfully')

        # Verify User is now ACTIVE
        user.refresh_from_db()
        self.assertEqual(user.status, User.Status.ACTIVE)
        self.assertTrue(user.is_active)

        # 4. Login SUCCESS
        login_response = self.client.post(self.login_url, login_payload)
        login_response_body = self._body(login_response)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response_body['data'])
        self.assertIn('refresh', login_response_body['data'])
        self.assertIn('token', login_response_body['data']['access'])

        token = login_response_body['data']['access']['token']

        # 5. Change Password (Require Old Password)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Attempt without old password (should fail)
        change_pass_payload_fail = {
            'new_password1': 'NewStrongPassword456!',
            'new_password2': 'NewStrongPassword456!'
        }
        fail_response = self.client.post(self.change_password_url, change_pass_payload_fail)
        self.assertEqual(fail_response.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt with old password (should success)
        change_pass_payload_success = {
            'old_password': self.user_data['password'],
            'new_password1': 'NewStrongPassword456!',
            'new_password2': 'NewStrongPassword456!'
        }
        success_response = self.client.post(self.change_password_url, change_pass_payload_success)
        self.assertEqual(success_response.status_code, status.HTTP_200_OK)

        # Verify Login with NEW password
        self.client.credentials() # Logout
        new_login_payload = {
            'email': self.user_data['email'],
            'password': 'NewStrongPassword456!'
        }
        new_login_response = self.client.post(self.login_url, new_login_payload)
        self.assertEqual(new_login_response.status_code, status.HTTP_200_OK)

    def test_verify_otp_invalid(self):
        """Test verification with wrong OTP"""
        # Create user manually and set inactive
        user = User.objects.create_user(
            email='wrongotp@example.com',
            password='testpassword'
        )
        user.status = User.Status.INACTIVE
        user.save()

        # Set a real OTP
        cache.set(f"otp_{user.email}", "123456", 300)

        payload = {
            'email': user.email,
            'otp': '000000' # Wrong OTP
        }
        response = self.client.post(self.verify_otp_url, payload)
        response_body = self._body(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_body['meta']['message'], 'Invalid or expired OTP')

    def test_verify_otp_expired(self):
        """Test verification with expired (non-existent) OTP"""
        user = User.objects.create_user(
            email='expiredotp@example.com',
            password='testpassword'
        )
        # Verify without setting cache
        payload = {
            'email': user.email,
            'otp': '123456'
        }
        response = self.client.post(self.verify_otp_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email_returns_400(self):
        """Registering with an existing email should return validation error, not 500."""
        User.objects.create_user(
            email='duplicate@example.com',
            password='StrongPassword123!',
            status=User.Status.ACTIVE,
        )

        payload = {
            'email': 'duplicate@example.com',
            'password1': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'display_name': 'Duplicate User'
        }
        response = self.client.post(self.register_url, payload)
        response_body = self._body(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response_body['meta']['message'],
            'A user is already registered with this e-mail address.',
        )


@override_settings(
    R2_ENDPOINT_URL='https://example.r2.cloudflarestorage.com',
    R2_REGION='auto',
    R2_BUCKET_NAME='test-bucket',
    R2_ACCESS_KEY_ID='test-access-key',
    R2_SECRET_ACCESS_KEY='test-secret-key',
    R2_PUBLIC_BASE_URL='https://storage.example.com',
    R2_AVATAR_PREFIX='avatar/',
    R2_MAX_UPLOAD_BYTES=1024 * 1024,
)
class AvatarUploadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='avatar@example.com',
            password='StrongPassword123!',
            status=User.Status.ACTIVE,
        )
        self.client.force_authenticate(user=self.user)
        self.avatar_url = reverse('users:avatar-delete')

    @staticmethod
    def _body(response):
        return response.json()

    @patch('apps.users.r2_storage._s3_client')
    def test_put_avatar_uploads_and_sets_profile(self, mock_s3_client):
        s3 = MagicMock()
        mock_s3_client.return_value = s3

        upload = SimpleUploadedFile(
            'avatar.png',
            b'\x89PNG\r\n\x1a\nfakepng',
            content_type='image/png',
        )
        response = self.client.put(self.avatar_url, {'file': upload}, format='multipart')
        body = self._body(response)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar', body['data'])
        self.assertIn('avatar_image_id', body['data'])
        self.assertTrue(body['data']['avatar'].startswith('https://storage.example.com/avatar/'))
        self.assertIn(f"/avatar/{self.user.id}/", body['data']['avatar'])

        # Ensure an object was uploaded to the expected bucket/prefix.
        self.assertTrue(s3.put_object.called)
        kwargs = s3.put_object.call_args.kwargs
        self.assertEqual(kwargs['Bucket'], 'test-bucket')
        self.assertTrue(kwargs['Key'].startswith(f"avatar/{self.user.id}/"))

        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar, body['data']['avatar'])
        self.assertEqual(self.user.avatar_image_id, body['data']['avatar_image_id'])

    @patch('apps.users.r2_storage._s3_client')
    def test_put_avatar_requires_file(self, mock_s3_client):
        response = self.client.put(self.avatar_url, {}, format='multipart')
        body = self._body(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(body['meta']['message'], 'file is required.')
        mock_s3_client.assert_not_called()
