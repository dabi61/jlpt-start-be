"""
Django settings for Nihongo Project.
"""
import os
import sys
import warnings
from pathlib import Path
from datetime import timedelta

import environ

# -----------------------------------------------------------------------------
# Third-party warning filters
# -----------------------------------------------------------------------------
# dj-rest-auth (current release) still imports deprecated allauth settings
# attributes at module import time. Keep this scoped to known upstream warnings.
warnings.filterwarnings(
    'ignore',
    message=r"app_settings\.USERNAME_REQUIRED is deprecated, use: app_settings\.SIGNUP_FIELDS\['username'\]\['required'\]",
    category=UserWarning,
    module=r'allauth\.account\.app_settings',
)
warnings.filterwarnings(
    'ignore',
    message=r"app_settings\.USERNAME_REQUIRED is deprecated, use: app_settings\.SIGNUP_FIELDS\['username'\]\['required'\]",
    category=UserWarning,
    module=r'dj_rest_auth\.registration\.serializers',
)
warnings.filterwarnings(
    'ignore',
    message=r"app_settings\.EMAIL_REQUIRED is deprecated, use: app_settings\.SIGNUP_FIELDS\['email'\]\['required'\]",
    category=UserWarning,
    module=r'allauth\.account\.app_settings',
)
warnings.filterwarnings(
    'ignore',
    message=r"app_settings\.EMAIL_REQUIRED is deprecated, use: app_settings\.SIGNUP_FIELDS\['email'\]\['required'\]",
    category=UserWarning,
    module=r'dj_rest_auth\.registration\.serializers',
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Application definition
INSTALLED_APPS = [
    # Jazzmin must be before django.contrib.admin
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'drf_spectacular',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Local apps
    'apps.users',
    'apps.practice',
    'apps.n3',
    'apps.n4',
    'apps.n5',
    'apps.courses',
    'apps.learning',
    'apps.vocabulary',
    'apps.grammar',
    'apps.kanjis',
    'apps.examples',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Site ID for allauth
SITE_ID = 1

# =============================================================================
# CORS Settings
# =============================================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only allow all origins in debug mode
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])

# =============================================================================
# REST Framework Settings
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'core.renderers.EnvelopedJSONRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'core.exception_handler.custom_exception_handler',
}

# =============================================================================
# Simple JWT Settings
# =============================================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=20),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',
}

# =============================================================================
# dj-rest-auth Settings
# =============================================================================
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': None,          # Return Access Token in Body
    'JWT_AUTH_REFRESH_COOKIE': None,  # Return Refresh Token in Body
    'USER_DETAILS_SERIALIZER': 'apps.users.serializers.UserSerializer',
    'REGISTER_SERIALIZER': 'apps.users.serializers.CustomRegisterSerializer',
    'LOGIN_SERIALIZER': 'apps.users.serializers.CustomLoginSerializer',
    'OLD_PASSWORD_FIELD_ENABLED': True,
}

# =============================================================================
# django-allauth Settings
# =============================================================================
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = None
ACCOUNT_ADAPTER = 'apps.users.adapters.CustomAccountAdapter'

# New-style allauth settings (avoid deprecated ACCOUNT_* auth flags)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']

# Email Backend for development (logging to console instead of sending real emails)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# =============================================================================
# Cloudflare Images Settings
# =============================================================================
CF_ACCOUNT_ID = env('CF_ACCOUNT_ID', default='')
CF_IMAGES_API_TOKEN = env('CF_IMAGES_API_TOKEN', default='')
CF_IMAGES_ACCOUNT_HASH = env('CF_IMAGES_ACCOUNT_HASH', default='')
CF_IMAGES_AVATAR_VARIANT = env('CF_IMAGES_AVATAR_VARIANT', default='avatar')
CF_IMAGES_TIMEOUT = env.int('CF_IMAGES_TIMEOUT', default=15)

# =============================================================================
# Cloudflare R2 (S3-compatible) Settings
# =============================================================================
# Used for direct-to-R2 uploads via presigned URLs.
R2_ENDPOINT_URL = env('R2_ENDPOINT_URL', default='')
R2_REGION = env('R2_REGION', default='auto')
R2_BUCKET_NAME = env('R2_BUCKET_NAME', default='')
R2_ACCESS_KEY_ID = env('R2_ACCESS_KEY_ID', default='')
R2_SECRET_ACCESS_KEY = env('R2_SECRET_ACCESS_KEY', default='')
R2_PUBLIC_BASE_URL = env('R2_PUBLIC_BASE_URL', default='')  # e.g. https://storage.jlpt.codes
R2_AVATAR_PREFIX = env('R2_AVATAR_PREFIX', default='avatar/')
R2_PRESIGNED_EXPIRES = env.int('R2_PRESIGNED_EXPIRES', default=600)
R2_MAX_UPLOAD_BYTES = env.int('R2_MAX_UPLOAD_BYTES', default=5242880)  # 5 MiB

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# =============================================================================
# drf-spectacular Settings (Swagger/OpenAPI)
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Nihongo Learning API',
    'DESCRIPTION': 'A production-ready API for Japanese language learning application. '
                   'Supports JWT and OAuth2 authentication.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SORT_OPERATIONS': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'auth'},
        {'name': 'users'},
        {'name': 'practice'},
        {'name': 'vocabulary'},
        {'name': 'kanjis'},
        {'name': 'grammar'},
        {'name': 'examples'},
        {'name': 'learning'},
        {'name': 'courses'},
        {'name': 'n3'},
        {'name': 'n4'},
        {'name': 'n5'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
    },
}

# =============================================================================
# Jazzmin Admin Settings
# =============================================================================
JAZZMIN_SETTINGS = {
    'site_title': 'Nihongo Admin',
    'site_header': 'Nihongo Learning',
    'site_brand': 'Nihongo',
    'welcome_sign': 'Welcome to Nihongo Learning Admin',
    'copyright': 'Nihongo Learning Platform',
    'search_model': ['users.User'],
    'topmenu_links': [
        {'name': 'Home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'API Docs', 'url': '/api/docs/', 'new_window': True},
    ],
    'show_sidebar': True,
    'navigation_expanded': True,
    'icons': {
        'auth': 'fas fa-users-cog',
        'users.User': 'fas fa-user',
        'courses.Course': 'fas fa-book',
        'learning.UserProgress': 'fas fa-chart-line',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-file',
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-dark',
    'accent': 'accent-primary',
    'navbar': 'navbar-dark',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': False,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'cosmo',
    'dark_mode_theme': 'darkly',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

# =============================================================================
# Cache Settings (Redis)
# =============================================================================
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Make unit tests self-contained (do not require a running Redis service).
if 'test' in sys.argv:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# =============================================================================
# Email Settings
# =============================================================================
# Default to console for dev, use SMTP for production
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Nihongo Learning <noreply@nihongo.com>')

# =============================================================================
# Celery Settings
# =============================================================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
