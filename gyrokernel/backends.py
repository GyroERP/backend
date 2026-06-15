"""Custom Django authentication backends for GyroERP."""

from __future__ import annotations

from django.contrib.auth.backends import ModelBackend


class LockoutBackend(ModelBackend):
    """
    Extends Django's ModelBackend with brute-force lockout enforcement.

    Before attempting the password check, consults LoginLog for:
      - A LOCKED event within the lock window  →  block immediately
      - N FAILED events within the window      →  create LOCKED event + block

    Thresholds are read from Django settings:
        GYROERP_BRUTE_FORCE_MAX_ATTEMPTS  (default: 10)
        GYROERP_BRUTE_FORCE_WINDOW_MINUTES (default: 10)

    ISO 27001 A.9.4.2 — Repeated failed log-on attempts must be restricted.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username:
            try:
                from gyrokernel.models.user_ext import LoginLog

                if LoginLog.is_locked_by_username(username):
                    return None  # account locked — block without trying password
            except Exception:
                pass  # DB unavailable during auth — fall through to standard check

        return super().authenticate(request, username=username, password=password, **kwargs)
