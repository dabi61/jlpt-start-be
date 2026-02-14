from allauth.account.adapter import DefaultAccountAdapter
from django.http import JsonResponse

from core.response_envelope import build_envelope

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
        return JsonResponse(
            build_envelope(
                code=403,
                message="Account is inactive. Please check your email for the verification code (OTP) to activate your account.",
                data={},
            ),
            status=403,
        )

    def respond_email_verification_sent(self, request, user):
        """
        Return JSON response when email verification is sent.
        """
        return JsonResponse(
            build_envelope(
                code=200,
                message="Verification email sent.",
                data={},
            ),
            status=200,
        )
