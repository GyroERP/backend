"""DRF authentication class for GyroERP API keys."""

from __future__ import annotations

import threading

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


# Thread-local storage for the authenticated API key so downstream code
# (permissions, throttling, audit) can access it without re-querying.
_local = threading.local()


def get_current_api_key():
    """Return the APIKey used in the current request, or None."""
    return getattr(_local, "api_key", None)


class APIKeyAuthentication(BaseAuthentication):
    """
    Authenticate via GyroERP API keys.

    Expected header:
        Authorization: ApiKey gyro_<prefix8>_<hex40>

    Returns (user, api_key_instance) on success.
    Returns None if the header is absent (passes to next authenticator).
    Raises AuthenticationFailed if the header is present but invalid.
    """

    KEYWORD = "ApiKey"

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(self.KEYWORD + " "):
            return None  # No API key header — try next authenticator

        raw_key = auth_header[len(self.KEYWORD) + 1:].strip()
        ip = self._get_client_ip(request)

        from gyrokernel.models.apikey import APIKey
        api_key = APIKey.authenticate(raw_key, ip_address=ip)

        if api_key is None:
            self._log_failure(raw_key, ip, request)
            raise AuthenticationFailed("Invalid or expired API key.")

        # Record usage asynchronously (best-effort — don't fail auth if this errors)
        try:
            api_key.record_usage(ip_address=ip)
        except Exception:
            pass

        # Store on thread-local for downstream access
        _local.api_key = api_key

        # Log successful API key auth
        self._log_success(api_key, ip, request)

        return (api_key.user, api_key)

    def authenticate_header(self, request) -> str:
        return self.KEYWORD

    @staticmethod
    def _get_client_ip(request) -> str | None:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def _log_failure(raw_key: str, ip: str | None, request) -> None:
        try:
            from gyrokernel.models.user_ext import LoginEvent, LoginLog

            LoginLog.record(
                event=LoginEvent.FAILED,
                username_attempted=f"[api_key:{raw_key[:13]}…]",
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
            )
        except Exception:
            pass

    @staticmethod
    def _log_success(api_key, ip: str | None, request) -> None:
        try:
            from gyrokernel.models.user_ext import LoginEvent, LoginLog

            LoginLog.record(
                event=LoginEvent.API_KEY,
                user=api_key.user,
                ip_address=ip,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:512],
                api_key=api_key,
            )
        except Exception:
            pass
