"""Signal definitions and handlers for the GyroERP kernel."""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save
from django.dispatch import Signal, receiver

# Fired after an app is activated via gyro_install_app
# kwargs: app_label (str), installed_app (InstalledApp)
app_installed = Signal()

# Fired before an app record is removed via gyro_uninstall_app
# kwargs: app_label (str)
app_uninstalled = Signal()


# ---------------------------------------------------------------------------
# Login / logout audit  — ISO 27001 A.12.4.1 (event logging)
# ---------------------------------------------------------------------------

@receiver(user_logged_in)
def _on_login_success(sender, request, user, **kwargs):
    try:
        from gyrokernel.models.user_ext import LoginEvent, LoginLog

        ip = _get_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""
        LoginLog.record(event=LoginEvent.SUCCESS, user=user, ip_address=ip, user_agent=ua)
    except Exception:
        pass


@receiver(user_login_failed)
def _on_login_failed(sender, credentials, request, **kwargs):
    try:
        from gyrokernel.models.user_ext import LoginEvent, LoginLog, _brute_force_max, _brute_force_window

        ip = _get_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""
        username = credentials.get("username", "") if credentials else ""

        log = LoginLog.record(
            event=LoginEvent.FAILED,
            username_attempted=username,
            ip_address=ip,
            user_agent=ua,
        )

        # Brute-force lockout: if a real user matched, check threshold.
        # ISO 27001 A.9.4.2 — restrict repeated failed log-on attempts.
        if log.user_id is None and username:
            from django.contrib.auth import get_user_model
            try:
                User = get_user_model()
                log.user = User.objects.get(username=username)
                log.save(update_fields=["user"])
            except Exception:
                return  # unknown username — nothing more to do

        if log.user_id:
            failed_count = LoginLog.recent_failed_count(
                log.user, window_minutes=_brute_force_window()
            )
            if failed_count >= _brute_force_max():
                LoginLog.record(
                    event=LoginEvent.LOCKED,
                    user=log.user,
                    username_attempted=username,
                    ip_address=ip,
                    user_agent=ua,
                )
    except Exception:
        pass


@receiver(user_logged_out)
def _on_logout(sender, request, user, **kwargs):
    """Record logout events for the audit trail. ISO 27001 A.12.4.1."""
    try:
        from gyrokernel.models.user_ext import LoginEvent, LoginLog

        if user is None:
            return
        ip = _get_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""
        LoginLog.record(event=LoginEvent.LOGOUT, user=user, ip_address=ip, user_agent=ua)
    except Exception:
        pass


def _get_ip(request) -> str | None:
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ---------------------------------------------------------------------------
# Audit trail for security-sensitive model changes
# ISO 27001 A.9.4.5 — privileged access management must be auditable
# ---------------------------------------------------------------------------

def _write_audit(instance, action: str) -> None:
    """Write a single AuditLog row for a sensitive model change."""
    try:
        from django.contrib.contenttypes.models import ContentType

        from gyrokernel.models.audit import AuditAction, AuditLog

        django_action = {
            "create": AuditAction.CREATE,
            "update": AuditAction.UPDATE,
            "delete": AuditAction.DELETE,
        }.get(action, AuditAction.CUSTOM)

        AuditLog.objects.create(
            action=django_action,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=str(instance.pk),
            object_repr=str(instance)[:500],
        )
    except Exception:
        pass


def _audit_save(sender, instance, created, **kwargs):
    _write_audit(instance, "create" if created else "update")


def _audit_delete(sender, instance, **kwargs):
    _write_audit(instance, "delete")


def _register_audit_signals() -> None:
    """
    Connect post_save / post_delete to models that require an audit trail.

    Called once from GyroKernelConfig.ready() via import of this module.
    Using a helper function avoids top-level imports before apps are loaded.
    """
    from gyrokernel.models.access_control import GroupExtension, ModelPermission
    from gyrokernel.models.access import RecordRule
    from gyrokernel.models.apikey import APIKey

    for model in (ModelPermission, GroupExtension, RecordRule, APIKey):
        post_save.connect(_audit_save, sender=model, weak=False)
        post_delete.connect(_audit_delete, sender=model, weak=False)


# Called from apps.py GyroKernelConfig.ready() after all models are loaded
_register_audit_signals()
