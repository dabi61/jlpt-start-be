import random
import string
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings

def generate_otp(email, length=6):
    """
    Generate a numeric OTP, save it to Redis with the email as key.
    OTP expires in 5 minutes.
    """
    otp = ''.join(random.choices(string.digits, k=length))
    # Save to cache with prefix 'otp_'
    cache.set(f"otp_{email}", otp, timeout=300)
    return otp

def send_otp_email(email, otp):
    """
    Send OTP to user's email.
    """
    subject = f"Verification Code: {otp}"
    message = f"Your verification code is: {otp}. It will expire in 5 minutes."
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(subject, message, from_email, [email])
