from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security ──────────────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [
"flasherp.in",
"[www.flasherp.in](http://www.flasherp.in)",
"localhost",
"127.0.0.1"
]


# ── Installed Apps ────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    # 'rest_framework_simplejwt.token_blacklist',  # ← removed: requires token_blacklist migration; causes 500 on refresh
    'corsheaders',

    # Local
    'backend',
    'login',
    'user',
    'payments',
    'usercontrol',
    'vehiclemaster',
    'vehiclemanagement',
    'challan',
    'claims',
    'imagecapture'
]

# ── Middleware ────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',          # must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # DISABLED — API uses JWT Bearer tokens
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

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

WSGI_APPLICATION = 'backend.wsgi.application'
ASGI_APPLICATION  = 'backend.asgi.application'

# ── Database ──────────────────────────────────────────────────


DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE'),
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# ── Password Validators ───────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Custom User Model ─────────────────────────────────────────
AUTH_USER_MODEL = 'login.User'

# ── Internationalisation ──────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ── Static / Media ────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── CSRF ──────────────────────────────────────────────────────────────────────
# CsrfViewMiddleware is disabled above (JWT Bearer token APIs don't need CSRF).
# CSRF_TRUSTED_ORIGINS kept as a safety net if it is ever re-enabled.
CSRF_TRUSTED_ORIGINS = [
    "https://flasherp.in",
    "https://www.flasherp.in",
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Django REST Framework ─────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

# ── Simple JWT ────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':    timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME':   timedelta(days=7),
    'ROTATE_REFRESH_TOKENS':    False,   # ← fixed: was True, caused 500 (needs token_blacklist migration)
    'BLACKLIST_AFTER_ROTATION': False,   # ← fixed: was True, caused 500 (needs token_blacklist migration)
    'UPDATE_LAST_LOGIN':        True,

    'ALGORITHM':   'HS256',
    'SIGNING_KEY': SECRET_KEY,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME':  'HTTP_AUTHORIZATION',
    'USER_ID_FIELD':     'id',
    'USER_ID_CLAIM':     'user_id',

    'TOKEN_OBTAIN_SERIALIZER': 'login.serializers.CustomTokenObtainPairSerializer',
}

# ── CORS ──────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "https://flasherp.in",
    "https://www.flasherp.in",
    "http://localhost:5173",    # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]