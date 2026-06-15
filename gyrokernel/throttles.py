"""DRF throttle classes for GyroERP."""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle

from gyrokernel.authentication import get_current_api_key


class APIKeyThrottle(SimpleRateThrottle):
    """
    Per-API-key rate limiting.

    Keyed by APIKey.pk so each key has its own rate bucket.
    Only fires when the request is authenticated via an API key.

    Configure rates in settings:
        REST_FRAMEWORK = {
            "DEFAULT_THROTTLE_RATES": {
                "apikey": "1000/hour",
            }
        }
    """

    scope = "apikey"

    def get_cache_key(self, request, view) -> str | None:
        api_key = get_current_api_key()
        if api_key is not None:
            return self.cache_format % {
                "scope": self.scope,
                "ident": str(api_key.pk),
            }
        return None  # not an API key request — skip this throttle


class SessionUserThrottle(SimpleRateThrottle):
    """
    Per-user rate limiting for session-authenticated requests.

    Prevents an authenticated browser/session user from hammering the API
    without limit — a gap that APIKeyThrottle doesn't cover.
    ISO 27001 A.13.1.1

    Configure rate in settings:
        REST_FRAMEWORK = {
            "DEFAULT_THROTTLE_RATES": {
                "user": "500/hour",
            }
        }
    """

    scope = "user"

    def get_cache_key(self, request, view) -> str | None:
        if get_current_api_key() is not None:
            return None  # already throttled by APIKeyThrottle
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                "scope": self.scope,
                "ident": str(request.user.pk),
            }
        return None  # anonymous — handled by AnonThrottle


class AnonThrottle(SimpleRateThrottle):
    """IP-based rate limit for unauthenticated requests."""

    scope = "anon"

    def get_cache_key(self, request, view) -> str | None:
        if request.user and request.user.is_authenticated:
            return None  # don't throttle authenticated users here
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
