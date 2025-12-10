# festive_births/settings.py

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ==========================================================
# CORE DEPLOYMENT SETTINGS
# ==========================================================
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
CSRF_TRUSTED_ORIGINS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

# ==========================================================
# APPLICATION DEFINITION
# ==========================================================
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'births.apps.BirthsConfig', 'accounts.apps.AccountsConfig',
    'crispy_forms', 'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'accounts.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'festive_births.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', 'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'festive_births.wsgi.application'

# ==========================================================
# DATABASE & CACHE
# ==========================================================
DATABASE_URL = os.environ.get('DATABASE_URL')
IS_PRODUCTION = 'RENDER' in os.environ

if DATABASE_URL:
    DATABASES = {'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600, ssl_require=IS_PRODUCTION)}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}

# ==========================================================
# AUTHENTICATION & SESSION MANAGEMENT
# ==========================================================
AUTHENTICATION_BACKENDS = ['accounts.backends.PersalAuthBackend', 'django.contrib.auth.backends.ModelBackend']
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'delivery_list'
LOGOUT_REDIRECT_URL = 'landing_page'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 1800  # Seconds (30 minutes * 60 seconds)
SESSION_SAVE_EVERY_REQUEST = True


# ==========================================================
# INTERNATIONALIZATION & STATIC FILES
# ==========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

# This is the folder where your dev static files live (e.g., your handwritten CSS)
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# This is the folder where collectstatic will gather all files for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# --- CONDITIONAL STATICFILES STORAGE ---
# By default, use Django's built-in staticfiles storage.
# This is perfect for development.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# If we are in production (DEBUG=False), then use WhiteNoise's storage.
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==========================================================
# PRODUCTION SECURITY SETTINGS
# ==========================================================
if IS_PRODUCTION:
    # Force all non-HTTPS requests to be redirected to HTTPS.
    SECURE_SSL_REDIRECT = True
    # Ensure the session cookie is only sent over HTTPS.
    SESSION_COOKIE_SECURE = True
    # Ensure the CSRF cookie is only sent over HTTPS.
    CSRF_COOKIE_SECURE = True

# ==========================================================
# EMAIL
# ==========================================================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# ==========================================================
# MISC / 3rd PARTY SETTINGS
# ==========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}