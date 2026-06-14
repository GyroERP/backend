"""DRF throttle classes for GyroERP."""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle

from gyrokernel.authentication import get_current_api_key


class APIKeyThrottle(SimpleRateThrottle):
    """
    Per-API-key rate limiting.

    Keyed by APIKey.pk so each key has its own rate bucket.
    Falls back to 'anon' rate for unauthenticated requests.

    Configure rates in settings:
        REST_FRAMEWORK = {
            "DEFAULT_THROTTLE_RATES": {
                "apikey": "1000/hour",
                "anon": "100/hour",
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
        # Fall back to IP-based throttling for session-authenticated requests
        return None


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
