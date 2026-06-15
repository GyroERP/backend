"""Production settings — ISO 27001 hardened."""

import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import SECRET_KEY, GYROERP_FERNET_KEY, env_bool, env_list

# ---------------------------------------------------------------------------
# Basics
# ---------------------------------------------------------------------------

DEBUG = env_bool("DJANGO_DEBUG", False)

if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY environment variable is required in production.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS environment variable is required in production."
    )

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# ---------------------------------------------------------------------------
# Encryption — ISO 27001 A.10.1.1
# ---------------------------------------------------------------------------

if not GYROERP_FERNET_KEY:
    raise ImproperlyConfigured(
        "GYROERP_FERNET_KEY environment variable is required in production to encrypt "
        "sensitive database fields (e.g. SMTP passwords). "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\""
    )

# ---------------------------------------------------------------------------
# Transport security (HTTPS)  — ISO 27001 A.13.2.1
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS — tell browsers to only use HTTPS for this domain for 1 year
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Cookie security  — ISO 27001 A.9.4.2
# ---------------------------------------------------------------------------

SESSION_COOKIE_SECURE = True        # transmit session cookie only over HTTPS
SESSION_COOKIE_HTTPONLY = True      # block JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = "Lax"    # CSRF mitigation for same-site navigation
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# ---------------------------------------------------------------------------
# HTTP security headers  — ISO 27001 A.14.1.2
# ---------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True          # X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER = True            # X-XSS-Protection: 1; mode=block (legacy browsers)
SECURE_REFERRER_POLICY = "strict-origin"    # Referrer-Policy — don't leak URL to third parties
X_FRAME_OPTIONS = "DENY"                    # X-Frame-Options — block clickjacking iframes

# Content-Security-Policy: restrict which resources the browser may load.
# Start restrictive; relax per-endpoint as the frontend evolves.
# ISO 27001 A.14.2.5
SECURE_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none';"
)

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)
