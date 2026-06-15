"""Lightweight CORS middleware for GyroERP (no external package required)."""

from __future__ import annotations

from django.conf import settings


class CORSMiddleware:
    """
    Adds Access-Control-* headers based on GYROERP_CORS_ALLOWED_ORIGINS.

    Configure in settings:
        GYROERP_CORS_ALLOWED_ORIGINS = ["https://app.example.com"]
        GYROERP_CORS_ALLOW_CREDENTIALS = False  # True only when using session auth cross-origin

    An empty GYROERP_CORS_ALLOWED_ORIGINS list blocks all cross-origin requests
    (default — correct for API-first backends that serve a same-origin frontend).

    ISO 27001 A.13.1.1 — Network access controls must restrict cross-origin requests.
    """

    _ALLOWED_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    _ALLOWED_HEADERS = "Authorization, Content-Type, X-Request-ID"
    _PREFLIGHT_MAX_AGE = "86400"

    def __init__(self, get_response):
        self.get_response = get_response
        self._allowed: set[str] = set(getattr(settings, "GYROERP_CORS_ALLOWED_ORIGINS", []))
        self._allow_credentials: bool = getattr(settings, "GYROERP_CORS_ALLOW_CREDENTIALS", False)

    def __call__(self, request):
        origin = request.META.get("HTTP_ORIGIN", "")

        # Respond to CORS preflight before the view runs
        if request.method == "OPTIONS" and origin and self._is_allowed(origin):
            return self._preflight_response(origin)

        response = self.get_response(request)

        if origin and self._is_allowed(origin):
            self._annotate(response, origin)

        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _is_allowed(self, origin: str) -> bool:
        return bool(self._allowed) and (origin in self._allowed or "*" in self._allowed)

    def _preflight_response(self, origin: str):
        from django.http import HttpResponse

        resp = HttpResponse()
        resp["Access-Control-Allow-Origin"] = origin
        resp["Access-Control-Allow-Methods"] = self._ALLOWED_METHODS
        resp["Access-Control-Allow-Headers"] = self._ALLOWED_HEADERS
        resp["Access-Control-Max-Age"] = self._PREFLIGHT_MAX_AGE
        resp["Vary"] = "Origin"
        if self._allow_credentials:
            resp["Access-Control-Allow-Credentials"] = "true"
        return resp

    def _annotate(self, response, origin: str) -> None:
        response["Access-Control-Allow-Origin"] = origin
        response["Vary"] = "Origin"
        if self._allow_credentials:
            response["Access-Control-Allow-Credentials"] = "true"
