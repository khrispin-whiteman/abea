import os
from pathlib import Path

from decouple import config
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-tcrfwn1$fd%#o_+e$5!5*r!rkq8y!h%$9%8&5#pzq2+r2u)yh_"
DEBUG = True

ALLOWED_HOSTS = ['abea1.onrender.com', 'abea1.org', 'www.abea1.org', '127.0.0.1']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    'accounts_app',
    'abea_app',

    'django_pesapal',
    'django_pesapalv3',
    'django_cleanup.apps.CleanupConfig',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "ABEA_Project.middleware.LanguageRedirectMiddleware",  # ADD THIS
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ABEA_Project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "ABEA_Project.context_processors.language_switcher_context",  # ADD THIS
            ],
        },
    },
]

WSGI_APPLICATION = "ABEA_Project.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = 'accounts_app.CustomUser'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# =========================
# INTERNATIONALIZATION
# =========================
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
    ("sw", _("Swahili")),
    ("pt", _("Portuguese")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

LANGUAGE_COOKIE_NAME = "django_language"
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = "Lax"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'africabmealliance24@gmail.com'
EMAIL_HOST_PASSWORD = 'hqxi ngpd vmhy tvbh'
DEFAULT_FROM_EMAIL = 'Africa Biomedical Engineering Alliance <noreply@dataidafrica.com>'

SITE_NAME = "Africa Biomedical Engineering Alliance"
DOMAIN = "abea1.org"
SITE_ID = 1

EMAIL_TIMEOUT = 30

FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'abea_app': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

MOBILE_MONEY_AUTH_ID = "01KH0SWDQ5HTEBQWNNVTY34BZ0"
MOBILE_MONEY_API_ENABLED = True
MOBILE_MONEY_MAX_RETRIES = 3
MOBILE_MONEY_RETRY_DELAY = 5

STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.getenv('PAYPAL_MODE', 'sandbox')
PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID', '')

PESAPAL_DEMO = config('PESAPAL_DEMO', default=True)
PESAPAL_CONSUMER_KEY = config('PESAPAL_CONSUMER_KEY')
PESAPAL_CONSUMER_SECRET = config('PESAPAL_CONSUMER_SECRET')
PESAPAL_BASE_URL = config('PESAPAL_BASE_URL')
PESAPAL_IPN_ID = config('PESAPAL_IPN_ID')
PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL = 'membership'

CSRF_TRUSTED_ORIGINS = [
    "https://abea1.onrender.com",
    "https://abea1.org",
    "https://www.abea1.org",
]