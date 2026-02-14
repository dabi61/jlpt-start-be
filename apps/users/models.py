"""
Custom User Model for Nihongo Learning Application.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class User(AbstractUser):
    """
    Custom User model with email as the unique identifier.
    Removes the username field and adds Japanese learning-specific fields.
    """

    class JLPTLevel(models.TextChoices):
        N6 = 'N6', 'Beginner'
        N5 = 'N5', 'N5 - Basic'
        N4 = 'N4', 'N4 - Elementary'
        N3 = 'N3', 'N3 - Intermediate'
        N2 = 'N2', 'N2 - Pre-Advanced'
        N1 = 'N1', 'N1 - Advanced'

    class Role(models.TextChoices):
        USER = 'USER', 'User'
        ADMIN = 'ADMIN', 'Admin'

    class LoginMethod(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        GOOGLE = 'GOOGLE', 'Google'
        FACEBOOK = 'FACEBOOK', 'Facebook'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        BANNED = 'BANNED', 'Banned'

    # Remove username field
    username = None

    # Email as primary identifier
    email = models.EmailField('email address', unique=True)

    # Profile fields
    display_name = models.CharField(
        'display name',
        max_length=50,
        blank=True,
        help_text='Display name for the user'
    )
    avatar = models.URLField(
        'avatar',
        blank=True,
        null=True,
        help_text='URL to user avatar image'
    )
    avatar_image_id = models.CharField(
        'avatar image id',
        max_length=128,
        blank=True,
        null=True,
        help_text='Cloudflare Images ID for current avatar'
    )

    # Auth & Role fields
    role = models.CharField(
        'role',
        max_length=10,
        choices=Role.choices,
        default=Role.USER
    )
    login_method = models.CharField(
        'login method',
        max_length=20,
        choices=LoginMethod.choices,
        default=LoginMethod.EMAIL
    )
    status = models.CharField(
        'status',
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    # Learning progress fields
    level = models.CharField(
        'JLPT level',
        max_length=2,
        choices=JLPTLevel.choices,
        default=JLPTLevel.N6,
        help_text='Current JLPT level target'
    )
    streak = models.PositiveIntegerField(
        'learning streak',
        default=0,
        help_text='Consecutive days of learning'
    )

    # Timestamps
    last_study_date = models.DateField(
        'last study date',
        null=True,
        blank=True,
        help_text='Last date the user completed a study session'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by USERNAME_FIELD

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Keep role/permission flags consistent. Superusers are always ADMIN.
        if self.is_superuser or self.role == self.Role.ADMIN:
            self.role = self.Role.ADMIN
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False

        self.is_active = self.status == self.Status.ACTIVE

        super().save(*args, **kwargs)

    @property
    def name(self):
        """Web-friendly alias for display_name."""
        if self.display_name:
            return self.display_name
        return self.email.split('@')[0]
