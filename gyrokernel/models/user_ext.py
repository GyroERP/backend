"""LoginLog and UserPreferences — auth audit trail and cross-ERP user settings."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from .base import TimestampedModel, UUIDModel


# ---------------------------------------------------------------------------
# Login audit
# ---------------------------------------------------------------------------

class LoginEvent(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    LOCKED = "locked", "Account Locked"
    API_KEY = "api_key", "API Key Auth"


class LoginLog(UUIDModel):
    """
    Authentication event log — one row per login attempt.

    Connected to Django signals (user_logged_in, user_login_failed) and
    to APIKeyAuthentication.  Used for audit and brute-force detection.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_logs",
        help_text="Null when the username was not found on a failed attempt",
    )
    username_attempted = models.CharField(
        max_length=255,
        blank=True,
        help_text="Raw username submitted — preserved even for unknown users",
    )
    event = models.CharField(max_length=10, choices=LoginEvent.choices, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    api_key = models.ForeignKey(
        "gyrokernel.APIKey",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="login_logs",
    )

    class Meta:
        verbose_name = "Login Log"
        verbose_name_plural = "Login Logs"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        user_label = str(self.user) if self.user_id else self.username_attempted or "?"
        return f"{self.event} — {user_label} @ {self.timestamp}"

    @classmethod
    def record(
        cls,
        event: str,
        user=None,
        username_attempted: str = "",
        ip_address: str | None = None,
        user_agent: str = "",
        api_key=None,
    ) -> "LoginLog":
        return cls.objects.create(
            user=user,
            username_attempted=username_attempted or (user.username if user else ""),
            event=event,
            ip_address=ip_address,
            user_agent=user_agent,
            api_key=api_key,
        )

    @classmethod
    def recent_failed_count(cls, user, window_minutes: int = 10) -> int:
        """Count failed login attempts for a user in the last window_minutes."""
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(minutes=window_minutes)
        return cls.objects.filter(
            user=user,
            event=LoginEvent.FAILED,
            timestamp__gte=cutoff,
        ).count()


# ---------------------------------------------------------------------------
# User preferences
# ---------------------------------------------------------------------------

class EmailDigestFrequency(models.TextChoices):
    NEVER = "never", "Never"
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"


class DisplayDensity(models.TextChoices):
    COMFORTABLE = "comfortable", "Comfortable"
    COMPACT = "compact", "Compact"


class Theme(models.TextChoices):
    LIGHT = "light", "Light"
    DARK = "dark", "Dark"
    SYSTEM = "system", "Follow System"


class FontSize(models.TextChoices):
    SMALL = "small", "Small"
    NORMAL = "normal", "Normal"
    LARGE = "large", "Large"


class UserPreferences(UUIDModel, TimestampedModel):
    """
    Per-user application preferences.

    Designed from cross-ERP analysis:
      Odoo · NetSuite · SAP S/4HANA · Oracle ERP Cloud · Salesforce · Dynamics 365

    Goals:
      - Users switching from any major ERP can port their preferences
      - Zero configuration required (sensible defaults throughout)
      - Module-specific prefs stored in JSONField `data` to avoid migrations
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )

    # --- Locale (cross-ERP universal) ---
    language = models.ForeignKey(
        "gyrokernel.Language",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Override account/browser language",
    )
    timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA timezone, e.g. 'America/New_York'",
    )
    date_format = models.CharField(
        max_length=30,
        blank=True,
        help_text="strftime pattern override, e.g. '%d/%m/%Y'",
    )
    time_format = models.CharField(
        max_length=30,
        blank=True,
        help_text="strftime pattern override, e.g. '%H:%M'",
    )
    decimal_point = models.CharField(
        max_length=1,
        blank=True,
        help_text="Override decimal separator (e.g. ',' for European locales)",
    )
    thousands_sep = models.CharField(
        max_length=1,
        blank=True,
        help_text="Override thousands separator",
    )
    currency = models.ForeignKey(
        "gyrokernel.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Preferred display currency (does not affect transactions)",
    )

    # --- Multi-company (NetSuite + SAP) ---
    default_company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Default company loaded on login for multi-company users",
    )

    # --- Notifications (Odoo + Salesforce + Dynamics) ---
    notify_email = models.BooleanField(default=True)
    notify_inapp = models.BooleanField(default=True)
    email_digest = models.CharField(
        max_length=10,
        choices=EmailDigestFrequency.choices,
        default=EmailDigestFrequency.NEVER,
    )
    notify_on_mention = models.BooleanField(default=True)
    notify_on_assign = models.BooleanField(default=True)
    notify_on_activity = models.BooleanField(
        default=True,
        help_text="Notify when tasks/activities are due or overdue",
    )
    notify_on_approval = models.BooleanField(
        default=True,
        help_text="Notify when purchases, leaves, or similar require approval",
    )

    # --- Display / UI (SAP + Oracle + Salesforce) ---
    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.SYSTEM,
    )
    display_density = models.CharField(
        max_length=15,
        choices=DisplayDensity.choices,
        default=DisplayDensity.COMFORTABLE,
    )
    records_per_page = models.IntegerField(
        default=25,
        help_text="Rows shown per page in list views (25 / 50 / 100)",
    )
    show_tutorials = models.BooleanField(
        default=True,
        help_text="Show in-app onboarding hints and guided tours",
    )
    keyboard_shortcuts = models.BooleanField(default=True)
    accessibility_high_contrast = models.BooleanField(default=False)
    font_size = models.CharField(
        max_length=10,
        choices=FontSize.choices,
        default=FontSize.NORMAL,
    )

    # --- Workflow (NetSuite + Odoo) ---
    email_signature = models.TextField(
        blank=True,
        help_text="Appended automatically to outgoing emails sent by this user",
    )
    out_of_office = models.BooleanField(default=False)
    out_of_office_message = models.TextField(blank=True)
    out_of_office_until = models.DateField(
        null=True,
        blank=True,
        help_text="Auto-disable OOO after this date",
    )

    # --- Security (Oracle + Dynamics) ---
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Placeholder for future 2FA implementation",
    )
    session_timeout_minutes = models.IntegerField(
        default=480,
        help_text="Idle session timeout in minutes; 0 = never expire",
    )

    # --- Open bag for module-specific preferences ---
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Module-specific preferences, e.g. {"sales": {"default_pricelist": "..."}}',
    )

    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"

    def __str__(self) -> str:
        return f"Preferences({self.user})"

    def get_module_pref(self, module: str, key: str, default=None):
        """Read a module-scoped preference from the data bag."""
        return (self.data or {}).get(module, {}).get(key, default)

    def set_module_pref(self, module: str, key: str, value) -> None:
        """Write a module-scoped preference to the data bag."""
        if not self.data:
            self.data = {}
        self.data.setdefault(module, {})[key] = value
        type(self).objects.filter(pk=self.pk).update(data=self.data)
