"""Session timeout middleware — enforces UserPreferences.session_timeout_minutes."""

from __future__ import annotations

from django.utils import timezone


class SessionTimeoutMiddleware:
    """
    Invalidates idle sessions that exceed the user's configured timeout.

    The last-activity timestamp is stored in the Django session. On each
    authenticated request, elapsed time is checked against the user's
    preference; if exceeded, the user is logged out (firing user_logged_out
    signal which writes a LOGOUT LoginLog entry).

    The timeout preference is cached in the session for 10 minutes to avoid
    a DB hit on every single request.

    ISO 27001 A.9.4.3 — Sessions must be locked after a period of inactivity.
    """

    _LAST_ACTIVITY_KEY = "_gyro_last_activity"
    _CACHED_TIMEOUT_KEY = "_gyro_timeout_minutes"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self._check_timeout(request)
        response = self.get_response(request)
        # Update last-activity after the view runs (only if still authenticated)
        if hasattr(request, "user") and request.user.is_authenticated:
            request.session[self._LAST_ACTIVITY_KEY] = timezone.now().isoformat()
        return response

    def _check_timeout(self, request) -> None:
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return

        last_str = request.session.get(self._LAST_ACTIVITY_KEY)
        if not last_str:
            return  # first request in this session

        timeout_minutes = self._resolve_timeout(request)
        if timeout_minutes == 0:
            return  # 0 = never expire

        from datetime import timedelta
        from django.utils.dateparse import parse_datetime

        last_activity = parse_datetime(last_str)
        if last_activity is None:
            return

        if timezone.now() - last_activity > timedelta(minutes=timeout_minutes):
            from django.contrib.auth import logout
            logout(request)  # fires user_logged_out signal → writes LoginLog

    def _resolve_timeout(self, request) -> int:
        """Read from session-cached pref; refresh when session key is absent."""
        cached = request.session.get(self._CACHED_TIMEOUT_KEY)
        if cached is not None:
            return int(cached)

        minutes = 480  # fallback: 8 hours
        try:
            minutes = request.user.preferences.session_timeout_minutes
        except Exception:
            pass

        request.session[self._CACHED_TIMEOUT_KEY] = minutes
        return minutes
