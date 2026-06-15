"""Shared Django settings for all GyroERP environments."""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.environ.get(name, "")
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    "gyrokernel",
]

MIDDLEWARE = [
    # CORS must be first so preflight responses are returned before any
    # auth/session middleware runs.  Configure GYROERP_CORS_ALLOWED_ORIGINS.
    "gyrokernel.middleware.cors.CORSMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "gyrokernel.middleware.request_id.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Session timeout must run after AuthenticationMiddleware so request.user is set.
    "gyrokernel.middleware.session_timeout.SessionTimeoutMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "gyroerp.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "gyroerp.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

# LockoutBackend wraps Django's ModelBackend with brute-force lockout.
# ISO 27001 A.9.4.2 — repeated failed log-on attempts must be restricted.
AUTHENTICATION_BACKENDS = [
    "gyrokernel.backends.LockoutBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# File upload limits  — ISO 27001 A.13.1.1 (resource exhaustion / DoS)
# ---------------------------------------------------------------------------

# Django's in-memory upload limit — files above this threshold are spooled to disk
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 MB

# GyroERP hard cap applied in Attachment.save() after computing file_size
GYROERP_MAX_UPLOAD_SIZE_MB = int(os.environ.get("GYROERP_MAX_UPLOAD_SIZE_MB", "25"))

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "gyrokernel.authentication.APIKeyAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "gyrokernel.permissions.GyroPermission",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "gyrokernel.throttles.APIKeyThrottle",
        "gyrokernel.throttles.SessionUserThrottle",
        "gyrokernel.throttles.AnonThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "apikey": "1000/hour",   # per API key  — ISO 27001 A.13.1.1
        "user": "500/hour",      # per session-authenticated user
        "anon": "100/hour",      # per IP for unauthenticated requests
    },
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "gyrokernel.pagination.GyroPageNumberPagination",
    "PAGE_SIZE": 25,
}

# ---------------------------------------------------------------------------
# Fernet field-level encryption (SMTP passwords, etc.)
# ISO 27001 A.10.1.1 — sensitive data at rest must be encrypted
# ---------------------------------------------------------------------------

# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Required in production (production.py will raise if absent).
GYROERP_FERNET_KEY = os.environ.get("GYROERP_FERNET_KEY", "")

# ---------------------------------------------------------------------------
# Brute-force lockout thresholds  — ISO 27001 A.9.4.2
# ---------------------------------------------------------------------------

GYROERP_BRUTE_FORCE_MAX_ATTEMPTS = int(os.environ.get("GYROERP_BRUTE_FORCE_MAX_ATTEMPTS", "10"))
GYROERP_BRUTE_FORCE_WINDOW_MINUTES = int(os.environ.get("GYROERP_BRUTE_FORCE_WINDOW_MINUTES", "10"))

# ---------------------------------------------------------------------------
# CORS — ISO 27001 A.13.1.1
# ---------------------------------------------------------------------------

# Comma-separated list of allowed origins, e.g. "https://app.example.com,https://admin.example.com"
# Empty by default (no cross-origin access).  Configure per environment.
GYROERP_CORS_ALLOWED_ORIGINS: list[str] = env_list("GYROERP_CORS_ALLOWED_ORIGINS", [])
GYROERP_CORS_ALLOW_CREDENTIALS: bool = env_bool("GYROERP_CORS_ALLOW_CREDENTIALS", False)

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TIMEZONE = "UTC"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("DJANGO_LOG_LEVEL", "INFO"),
    },
}
