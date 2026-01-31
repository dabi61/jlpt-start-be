from allauth.account.adapter import DefaultAccountAdapter
from rest_framework.response import Response
from rest_framework import status
import json
from django.http import HttpResponse

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom Account Adapter to handle API responses instead of redirects
    for inactive users or email verification.
    """

    def respond_user_inactive(self, request, user):
        """
        Return JSON response when user is inactive (instead of redirecting).
        """
        # Since this is called from within a view, we often need to return an HttpResponse
        # that DRF can handle or a simple HttpResponse with JSON.
        response_data = {
            "error": "Account is inactive.",
            "detail": "Please check your email for the verification code (OTP) to activate your account."
        }
        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json",
            status=403
        )

    def respond_email_verification_sent(self, request, user):
        """
        Return JSON response when email verification is sent.
        """
        return HttpResponse(
            json.dumps({"detail": "Verification email sent."}),
            content_type="application/json",
            status=200
        )
