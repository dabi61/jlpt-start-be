import json
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework import status

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

    def test_full_auth_flow(self):
        """
        Test the complete flow: Register -> Verify OTP -> Login -> Change Password
        """
        # 1. Registration
        response = self.client.post(self.register_url, self.register_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Verification Code has been sent', response.data['detail'])
        self.assertNotIn('key', response.data)  # Ensure no token is returned
        self.assertNotIn('access', response.data)

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
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(verify_response.data['message'], 'Account verified successfully')

        # Verify User is now ACTIVE
        user.refresh_from_db()
        self.assertEqual(user.status, User.Status.ACTIVE)
        self.assertTrue(user.is_active)

        # 4. Login SUCCESS
        login_response = self.client.post(self.login_url, login_payload)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)

        token = login_response.data['access']

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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Invalid or expired OTP')

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
