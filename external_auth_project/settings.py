from pathlib import Path
from venv import logger
import environ
import os

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_results',
    'auth_app',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auth_app.middleware.SecurityHeadersMiddleware',
]

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
STATIC_URL = '/static/' 
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Static files directories
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
MEDIA_DIR = BASE_DIR / 'media'
MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_AGE = 60 * 60 * 24
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_NAME = 'hemis_csrf_token'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# Production (HTTPS + nginx) da .env orqali yoqing:
# SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_REFERRER_POLICY = 'same-origin'

# Rate limit (login / submit / messages)
RATE_LIMIT_LOGIN = env.int('RATE_LIMIT_LOGIN', default=8)
RATE_LIMIT_LOGIN_WINDOW = env.int('RATE_LIMIT_LOGIN_WINDOW', default=60)
RATE_LIMIT_SURVEY_SUBMIT = env.int('RATE_LIMIT_SURVEY_SUBMIT', default=20)
RATE_LIMIT_MESSAGE = env.int('RATE_LIMIT_MESSAGE', default=15)
ROOT_URLCONF = 'external_auth_project.urls'

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

CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND')
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env('REDIS_URL', default="redis://redis:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

EXTERNAL_API_BASE_URL = env('EXTERNAL_API_BASE_URL', default="https://student.nspi.uz/rest")
EXTERNAL_API_LOGIN_ENDPOINT = f"{EXTERNAL_API_BASE_URL}/v1/auth/login"
EXTERNAL_API_ACCOUNT_ME_ENDPOINT = f"{EXTERNAL_API_BASE_URL}/v1/account/me"
EXTERNAL_API_REFRESH_TOKEN_ENDPOINT = f"{EXTERNAL_API_BASE_URL}/v1/auth/refresh-token" 
REQUESTS_VERIFY_SSL = env.bool('REQUESTS_VERIFY_SSL', default=True)

API_TOKEN_REFRESH_THRESHOLD_SECONDS = 10 * 60 

HEMIS_ADMIN_API_TOKEN  = env('HEMIS_ADMIN_API_TOKEN',  default=None)
HEMIS_SYSTEM_API_TOKEN = env('HEMIS_SYSTEM_API_TOKEN', default=None)

EXTERNAL_API_LOGOUT_ENDPOINT = env('EXTERNAL_API_LOGOUT_ENDPOINT', default=None)

# ── HEMIS OAuth2 ──────────────────────────────────────────────────────────────
# Talaba portali:  https://student.nspi.uz
# Hodim portali:   https://hemis.nspi.uz
HEMIS_STUDENT_OAUTH_BASE_URL  = env('HEMIS_STUDENT_OAUTH_BASE_URL',  default='https://student.nspi.uz')
HEMIS_EMPLOYEE_OAUTH_BASE_URL = env('HEMIS_EMPLOYEE_OAUTH_BASE_URL', default='https://hemis.nspi.uz')

# Yagona client (ikkala portal uchun bir xil bo'lsa)
HEMIS_OAUTH_CLIENT_ID     = env('HEMIS_OAUTH_CLIENT_ID',     default='')
HEMIS_OAUTH_CLIENT_SECRET = env('HEMIS_OAUTH_CLIENT_SECRET', default='')

# Alohida talaba client (bo'lsa — ustunlik beradi)
HEMIS_STUDENT_OAUTH_CLIENT_ID     = env('HEMIS_STUDENT_OAUTH_CLIENT_ID',     default='')
HEMIS_STUDENT_OAUTH_CLIENT_SECRET = env('HEMIS_STUDENT_OAUTH_CLIENT_SECRET', default='')

# Callback URL — production da to'liq domen (masalan: https://survey.nspi.uz/oauth/callback/)
HEMIS_OAUTH_REDIRECT_URI = env('HEMIS_OAUTH_REDIRECT_URI', default='http://localhost:8000/oauth/callback/')

# OAuth scope (bo'sh = default)
HEMIS_OAUTH_SCOPE = env('HEMIS_OAUTH_SCOPE', default='')

WSGI_APPLICATION = 'external_auth_project.wsgi.application'

LOGIN_URL = 'login'  
LOGIN_REDIRECT_URL = 'home'  
DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': env('DB_NAME', default='survey_prod_db'),
        'USER': env('DB_USER', default='survey_user'),
        # Default zaif parol olib tashlandi — majburiy env
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='db'),
        'PORT': env('DB_PORT', default='5432'),
    }
}


if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    DATABASES['default'].pop('USER', None)
    DATABASES['default'].pop('PASSWORD', None)
    DATABASES['default'].pop('HOST', None)
    DATABASES['default'].pop('PORT', None)
elif DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    DATABASES['default'].setdefault('OPTIONS', {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4', 
    })
    if DATABASES['default'].get('PORT'):
        try:
            DATABASES['default']['PORT'] = int(DATABASES['default']['PORT'])
        except ValueError:
            logger.warning(f"DB_PORT qiymati ({DATABASES['default']['PORT']}) raqam emas. MySQL uchun standart port ishlatiladi yoki xatolik yuz berishi mumkin.")
            DATABASES['default']['PORT'] = '3306' 


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# WhiteNoise sozlamalari CSS map fayl muammolarini hal qilish uchun
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['js', 'css']
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False

LANGUAGE_CODE = 'uz'

LANGUAGES = [
    ('uz', "O'zbek"),
    ('ru', 'Русский'),
    ('en', 'English'),
    ('kaa', 'Qaraqalpaq'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SESSION_COOKIE_AGE = 24 * 60 * 60  

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            # Non-root konteynerda yozish uchun /tmp (FIND-015)
            'filename': env('DJANGO_LOG_FILE', default='/tmp/django_app.log'),
            'maxBytes': 1024*1024*5,
            'backupCount': 2,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'auth_app': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'requests': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    }
}