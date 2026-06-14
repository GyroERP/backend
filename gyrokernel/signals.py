"""Signal definitions and handlers for the GyroERP kernel."""

from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import Signal, receiver

# Fired after an app is activated via gyro_install_app
# kwargs: app_label (str), installed_app (InstalledApp)
app_installed = Signal()

# Fired before an app record is removed via gyro_uninstall_app
# kwargs: app_label (str)
app_uninstalled = Signal()


# ---------------------------------------------------------------------------
# Login audit — connected to Django's built-in auth signals
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
        from gyrokernel.models.user_ext import LoginEvent, LoginLog

        ip = _get_ip(request)
        ua = request.META.get("HTTP_USER_AGENT", "")[:512] if request else ""
        username = credentials.get("username", "") if credentials else ""
        LoginLog.record(event=LoginEvent.FAILED, username_attempted=username, ip_address=ip, user_agent=ua)
    except Exception:
        pass


def _get_ip(request) -> str | None:
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
