"""DRF permission class combining model-level ACL and API key scope checks."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from gyrokernel.authentication import get_current_api_key


_METHOD_TO_ACTION = {
    "GET": "read",
    "HEAD": "read",
    "OPTIONS": "read",
    "POST": "create",
    "PUT": "write",
    "PATCH": "write",
    "DELETE": "delete",
}


class GyroPermission(BasePermission):
    """
    Unified permission gate for GyroERP API views.

    Checks (in order):
      1. Is user authenticated?
      2. Does the API key's scope permit the HTTP method?  (if key-authenticated)
      3. Does ModelPermission allow this user+group to perform this action?

    Views can declare `gyro_model_name` to specify which model to check;
    if absent, the viewset's `queryset.model` is used as a fallback.

    Views that want to skip model permission checks (e.g. meta endpoints)
    can set `gyro_skip_permission = True`.
    """

    def has_permission(self, request, view) -> bool:
        # Unauthenticated — deny
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers bypass all checks
        if request.user.is_superuser:
            return True

        # Skip flag for special views
        if getattr(view, "gyro_skip_permission", False):
            return True

        # --- API key scope check ---
        api_key = get_current_api_key()
        if api_key is not None:
            if not api_key.allows_method(request.method):
                return False
            model_name = self._get_model_name(view)
            if model_name and not api_key.allows_model(model_name):
                return False

        # --- Model-level permission check ---
        model_name = self._get_model_name(view)
        if model_name:
            from gyrokernel.models.access_control import ModelPermission

            action = _METHOD_TO_ACTION.get(request.method.upper(), "read")
            if not ModelPermission.check_access(model_name, request.user, action):
                return False

        return True

    @staticmethod
    def _get_model_name(view) -> str | None:
        # Explicit declaration takes precedence
        model_name = getattr(view, "gyro_model_name", None)
        if model_name:
            return model_name
        # Fall back to queryset model
        qs = getattr(view, "queryset", None)
        if qs is not None and hasattr(qs, "model"):
            opts = qs.model._meta
            return f"{opts.app_label}.{opts.object_name}"
        return None
