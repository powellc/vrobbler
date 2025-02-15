import os
import sys
from pathlib import Path


import dj_database_url
from dotenv import load_dotenv

TRUTHY = ("true", "1", "t")

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))

load_dotenv("vrobbler.conf.test")

# Build paths inside the project like this: BASE_DIR / 'subdir'.


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("VROBBLER_SECRET_KEY", "not-a-secret-234lkjasdflj132")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("VROBBLER_DEBUG", "false").lower() in TRUTHY

TAGGIT_CASE_INSENSITIVE = True

KEEP_DETAILED_SCROBBLE_LOGS = os.getenv(
    "VROBBLER_KEEP_DETAILED_SCROBBLE_LOGS", False
)

# Key must be 16, 24 or 32 bytes long and will be converted to a byte stream
ENCRYPTED_FIELD_KEY = os.getenv(
    "VROBBLER_ENCRYPTED_FIELD_KEY", "12345678901234567890123456789012"
)

DJANGO_ENCRYPTED_FIELD_KEY = bytes(ENCRYPTED_FIELD_KEY, "utf-8")

# Should we cull old in-progress scrobbles that are beyond the wait period for resuming?
DELETE_STALE_SCROBBLES = (
    os.getenv("VROBBLER_DELETE_STALE_SCROBBLES", "true").lower() in TRUTHY
)

# Used to dump data coming from srobbling sources, helpful for building new inputs
DUMP_REQUEST_DATA = (
    os.getenv("VROBBLER_DUMP_REQUEST_DATA", "false").lower() in TRUTHY
)

THESPORTSDB_API_KEY = os.getenv("VROBBLER_THESPORTSDB_API_KEY", "2")
THEAUDIODB_API_KEY = os.getenv("VROBBLER_THEAUDIODB_API_KEY", "2")
TMDB_API_KEY = os.getenv("VROBBLER_TMDB_API_KEY", "")
LASTFM_API_KEY = os.getenv("VROBBLER_LASTFM_API_KEY")
LASTFM_SECRET_KEY = os.getenv("VROBBLER_LASTFM_SECRET_KEY")
IGDB_CLIENT_ID = os.getenv("VROBBLER_IGDB_CLIENT_ID")
IGDB_CLIENT_SECRET = os.getenv("VROBBLER_IGDB_CLIENT_SECRET")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TIME_ZONE = os.getenv("VROBBLER_TIME_ZONE", "US/Eastern")

ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    os.getenv("VROBBLER_TRUSTED_ORIGINS", "http://localhost:8000")
]
X_FRAME_OPTIONS = "SAMEORIGIN"

REDIS_URL = os.getenv("VROBBLER_REDIS_URL", None)
if REDIS_URL:
    print(f"Sending tasks to redis@{REDIS_URL.split('@')[-1]}")
else:
    print("Eagerly running all tasks")

CELERY_TASK_ALWAYS_EAGER = (
    os.getenv("VROBBLER_SKIP_CELERY", "false").lower() in TRUTHY
)
CELERY_BROKER_URL = REDIS_URL if REDIS_URL else "memory://localhost/"
CELERY_RESULT_BACKEND = "django-db"
CELERY_TIMEZONE = os.getenv("VROBBLER_TIME_ZONE", "US/Eastern")
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
    "markdownify",
    "imagekit",
    "storages",
    "taggit",
    "rest_framework.authtoken",
    "encrypted_field",
    "profiles",
    "scrobbles",
    "videos",
    "music",
    "podcasts",
    "sports",
    "books",
    "boardgames",
    "bricksets",
    "videogames",
    "locations",
    "webpages",
    "trails",
    "lifeevents",
    "moods",
    "mathfilters",
    "rest_framework",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_celery_results",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "scrobbles.context_processors.now_playing",
            ],
        },
    },
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

WSGI_APPLICATION = "vrobbler.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("VROBBLER_DATABASE_URL", "sqlite:///db.sqlite3"),
        conn_max_age=600,
    ),
}


db_str = ""
if "sqlite" in DATABASES["default"]["ENGINE"]:
    db_str = f"Connected to sqlite@{DATABASES['default']['NAME']}"
if "postgresql" in DATABASES["default"]["ENGINE"]:
    db_str = f"Connected to postgres@{DATABASES['default']['HOST']}/{DATABASES['default']['NAME']}"
if db_str:
    print(db_str)


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
if REDIS_URL:
    CACHES["default"]["BACKEND"] = "django_redis.cache.RedisCache"
    CACHES["default"]["LOCATION"] = REDIS_URL

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# We have to ignore content negotiation because Jellyfin is a bad actor
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.AllowAny",),
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_CONTENT_NEGOTIATION_CLASS": "vrobbler.negotiation.IgnoreClientContentNegotiation",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend"
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 200,
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

TIME_ZONE = os.getenv("VROBBLER_TIME_ZONE", "America/New_York")

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/
#
from storages.backends import s3boto3

USE_S3_STORAGE = os.getenv("VROBBLER_USE_S3", "False").lower() in TRUTHY

if USE_S3_STORAGE:
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY")

    S3_ROOT = "/".join([AWS_S3_ENDPOINT_URL, AWS_STORAGE_BUCKET_NAME])
    print(f"Storing media on S3 at {S3_ROOT}")

    DEFAULT_FILE_STORAGE = "vrobbler.storages.MediaStorage"
    STATICFILES_STORAGE = "vrobbler.storages.StaticStorage"
    STATIC_URL = S3_ROOT + "/static/"
    MEDIA_URL = S3_ROOT + "/media/"

else:
    STATIC_ROOT = os.getenv(
        "VROBBLER_STATIC_ROOT", os.path.join(PROJECT_ROOT, "static")
    )
    MEDIA_ROOT = os.getenv(
        "VROBBLER_MEDIA_ROOT", os.path.join(PROJECT_ROOT, "media")
    )
    STATIC_URL = os.getenv("VROBBLER_STATIC_URL", "/static/")
    MEDIA_URL = os.getenv("VROBBLER_MEDIA_URL", "/media/")


JSON_LOGGING = os.getenv("VROBBLER_JSON_LOGGING", "false").lower() in TRUTHY
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
        "sql": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "".join([LOG_FILE_PATH, "vrobbler_sql.", LOG_TYPE]),
            "formatter": LOG_TYPE,
            "level": LOG_LEVEL,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "".join([LOG_FILE_PATH, "vrobbler.", LOG_TYPE]),
            "formatter": LOG_TYPE,
            "level": LOG_LEVEL,
        },
    },
    "loggers": {
        # Quiet down our console a little
        "django": {
            "handlers": ["null"],
            "propagate": True,
        },
        "django.db.backends": {"handlers": ["null"]},
        "django.server": {"handlers": ["null"]},
        "pylast": {"handlers": ["null"], "propagate": False},
        "musicbrainzngs": {"handlers": ["null"], "propagate": False},
        "httpx": {"handlers": ["null"], "propagate": False},
        "vrobbler": {
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

LOG_TO_CONSOLE = (
    os.getenv("VROBBLER_LOG_TO_CONSOLE", "false").lower() in TRUTHY
)
if LOG_TO_CONSOLE:
    LOGGING["loggers"]["django"]["handlers"] = ["console"]
    LOGGING["loggers"]["vrobbler"]["handlers"] = ["console"]
