import os
import sys
from pathlib import Path

import dj_database_url
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'apps'))

# Tap vrobbler.conf if it's available
if os.path.exists("vrobbler.conf"):
    load_dotenv("vrobbler.conf")
elif os.path.exists("/etc/vrobbler.conf"):
    load_dotenv("/etc/vrobbler.conf")
elif os.path.exists("/usr/local/etc/vrobbler.conf"):
    load_dotenv("/usr/local/etc/vrobbler.conf")

# Build paths inside the project like this: BASE_DIR / 'subdir'.


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("VROBBLER_SECRET_KEY", "not-a-secret-234lkjasdflj132")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("VROBBLER_DEBUG", False)

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

KEEP_DETAILED_SCROBBLE_LOGS = os.getenv(
    "VROBBLER_KEEP_DETAILED_SCROBBLE_LOGS", False
)

PODCAST_COMPLETION_PERCENT = os.getenv(
    "VROBBLER_PODCAST_COMPLETION_PERCENT", 25
)
MUSIC_COMPLETION_PERCENT = os.getenv("VROBBLER_MUSIC_COMPLETION_PERCENT", 90)

# Should we cull old in-progress scrobbles that are beyond the wait period for resuming?
DELETE_STALE_SCROBBLES = os.getenv("VROBBLER_DELETE_STALE_SCROBBLES", True)

# Used to dump data coming from srobbling sources, helpful for building new inputs
DUMP_REQUEST_DATA = os.getenv("VROBBLER_DUMP_REQUEST_DATA", False)

VIDEO_BACKOFF_MINUTES = os.getenv("VROBBLER_VIDEO_BACKOFF_MINUTES", 15)
MUSIC_BACKOFF_SECONDS = os.getenv("VROBBLER_VIDEO_BACKOFF_SECONDS", 1)

# If you stop waching or listening to a track, how long should we wait before we
# give up on the old scrobble and start a new one? This could also be considered
# a "continue in progress scrobble" time period. So if you pause the media and
# start again, should it be a new scrobble.
VIDEO_WAIT_PERIOD_DAYS = os.getenv("VROBBLER_VIDEO_WAIT_PERIOD_DAYS", 1)
MUSIC_WAIT_PERIOD_MINUTES = os.getenv("VROBBLER_VIDEO_BACKOFF_MINUTES", 1)

THESPORTSDB_API_KEY = os.getenv("VROBBLER_THESPORTSDB_API_KEY", "2")
THESPORTSDB_BASE_URL = os.getenv(
    "VROBBLER_THESPORTSDB_BASE_URL", "https://www.thesportsdb.com/api/v1/json/"
)
TMDB_API_KEY = os.getenv("VROBBLER_TMDB_API_KEY", "")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TIME_ZONE = os.getenv("VROBBLER_TIME_ZONE", "EST")

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    os.getenv("VROBBLER_TRUSTED_ORIGINS", "http://localhost:8000")
]
X_FRAME_OPTIONS = "SAMEORIGIN"

REDIS_URL = os.getenv("VROBBLER_REDIS_URL", None)

CELERY_TASK_ALWAYS_EAGER = os.getenv("VROBBLER_SKIP_CELERY", False)
CELERY_BROKER_URL = REDIS_URL if REDIS_URL else "memory://localhost/"
CELERY_RESULT_BACKEND = "django-db"
CELERY_TIMEZONE = os.getenv("VROBBLER_TIME_ZONE", "EST")
CELERY_TASK_TRACK_STARTED = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",
    "django_filters",
    "django_extensions",
    'rest_framework.authtoken',
    "scrobbles",
    "videos",
    "music",
    "podcasts",
    "sports",
    "rest_framework",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_celery_results",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.gzip.GZipMiddleware",
]

ROOT_URLCONF = "vrobbler.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(PROJECT_ROOT.joinpath("templates"))],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "videos.context_processors.video_lists",
                "music.context_processors.music_lists",
            ],
        },
    },
]

WSGI_APPLICATION = "vrobbler.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("VROBBLER_DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
    ),
}
if TESTING:
    DATABASES = {
        "default": dj_database_url.config(default="sqlite:///testdb.sqlite3")
    }


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
if REDIS_URL:
    CACHES["default"][
        "BACKEND"
    ] = "django.core.cache.backends.redis.RedisCache"
    CACHES["default"]["LOCATION"] = REDIS_URL

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        #'rest_framework.authentication.BasicAuthentication',
        #'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_CONTENT_NEGOTIATION_CLASS': 'vrobbler.negotiation.IgnoreClientContentNegotiation',
    "PAGE_SIZE": 100,
}

LOGIN_REDIRECT_URL = "/"

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.getenv("VROBBLER_TIME_ZONE", "EST")

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.getenv(
    "VROBBLER_STATIC_ROOT", os.path.join(PROJECT_ROOT, "static")
)
if not DEBUG:
    STATICFILES_STORAGE = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv(
    "VROBBLER_MEDIA_ROOT", os.path.join(PROJECT_ROOT, "media")
)

JSON_LOGGING = os.getenv("VROBBLER_JSON_LOGGING", False)
LOG_TYPE = "json" if JSON_LOGGING else "log"

default_level = "INFO"
if DEBUG:
    default_level = "DEBUG"

LOG_LEVEL = os.getenv("VROBBLER_LOG_LEVEL", default_level)
LOG_FILE_PATH = os.getenv("VROBBLER_LOG_FILE_PATH", "/tmp/")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {
        "handlers": ["console", "file"],
        "level": LOG_LEVEL,
        "propagate": True,
    },
    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            # \r returns caret to line beginning, in tests this eats the silly dot that removes
            # the beautiful alignment produced below
            "format": "\r"
            "{log_color}{levelname:8s}{reset} "
            "{bold_cyan}{name}{reset}:"
            "{fg_bold_red}{lineno}{reset} "
            "{thin_yellow}{funcName} "
            "{thin_white}{message}"
            "{reset}",
            "style": "{",
        },
        "log": {"format": "%(asctime)s %(levelname)s %(message)s"},
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(levelname)s %(name) %(funcName) %(lineno) %(asctime)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "color",
            "level": LOG_LEVEL,
        },
        "null": {
            "class": "logging.NullHandler",
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "".join([LOG_FILE_PATH, "vrobbler.log"]),
            "formatter": LOG_TYPE,
            "level": LOG_LEVEL,
        },
        "requests_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "".join([LOG_FILE_PATH, "vrobbler_requests.log"]),
            "formatter": LOG_TYPE,
            "level": LOG_LEVEL,
        },
    },
    "loggers": {
        # Quiet down our console a little
        "django": {
            "handlers": ["file"],
            "propagate": True,
        },
        "django.db.backends": {"handlers": ["null"]},
        "django.server": {"handlers": ["null"]},
        "vrobbler": {
            "handlers": ["console", "file"],
            "propagate": True,
        },
    },
}

if DEBUG:
    # We clear out a db with lots of games all the time in dev
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 3000
