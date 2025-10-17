from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ==========================================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================================
# Load variables from .env file for local development.
# On Render, this file won't exist, and it will use dashboard environment variables.
load_dotenv(os.path.join(BASE_DIR, '.env'))

# ==========================================================
# CORE DEPLOYMENT SETTINGS
# ==========================================================
# Reads the secret key from an environment variable.
SECRET_KEY = os.environ.get('SECRET_KEY')

# Reads the debug setting from an environment variable. Defaults to False for production safety.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# --- CORRECTED ALLOWED_HOSTS ---
# Starts with local hosts, then adds Render's hostname if it exists.
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ==========================================================
# NEW: CSRF TRUSTED ORIGINS SETTING
# ==========================================================
# This tells Django to trust POST requests originating from your Render domain.
# It is required for HTTPS deployments.
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS = (f'https://{RENDER_EXTERNAL_HOSTNAME}') 

# ==========================================================
# APPLICATION DEFINITION
# ==========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Our apps
    'births.apps.BirthsConfig',
    'accounts.apps.AccountsConfig',
    # 3rd Party Apps
    'crispy_forms',
    'crispy_bootstrap5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise middleware for serving static files in production
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
        'DIRS': [BASE_DIR / 'templates'], 
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

WSGI_APPLICATION = 'festive_births.wsgi.application'

# ==========================================================
# DATABASE
# ==========================================================
# Uses DATABASE_URL from environment if available (for Render/production),
# otherwise falls back to local sqlite3.
if 'DATABASE_URL' in os.environ:
    DATABASES = {'default': dj_database_url.config(conn_max_age=600, ssl_require=True)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==========================================================
# AUTHENTICATION & PASSWORD VALIDATION
# ==========================================================
AUTHENTICATION_BACKENDS = [
    'accounts.backends.PersalAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'delivery_list'
LOGOUT_REDIRECT_URL = 'landing_page'

# ==========================================================
# INTERNATIONALIZATION & STATIC FILES
# ==========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==========================================================
# EMAIL (for Password Resets)
# ==========================================================
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

# ==========================================================
# MISC / 3rd PARTY SETTINGS
# ==========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
