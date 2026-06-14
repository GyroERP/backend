"""App installation registry model."""

from django.conf import settings
from django.db import models

from .base import TimestampedModel, UUIDModel


class AppState(models.TextChoices):
    INSTALLED = "installed", "Installed"
    UNINSTALLING = "uninstalling", "Uninstalling"
    ERROR = "error", "Error"


class InstalledApp(UUIDModel, TimestampedModel):
    """
    Tracks which GyroERP apps are logically active in this installation.

    Django's INSTALLED_APPS is static (set at startup). This model represents
    the dynamic layer: which apps have been activated and are available at runtime
    for API access, data operations, and feature flags.
    """

    app_label = models.CharField(
        max_length=100,
        unique=True,
        help_text="Django app_label, e.g. 'accounting'",
    )
    gyro_name = models.CharField(max_length=255, help_text="Human-readable name")
    version = models.CharField(max_length=20, default="1.0.0")
    state = models.CharField(
        max_length=20,
        choices=AppState.choices,
        default=AppState.INSTALLED,
        db_index=True,
    )
    depends = models.JSONField(default=list, help_text="app_labels this app depends on")
    category = models.CharField(max_length=100, default="Generic")
    description = models.TextField(blank=True)
    installed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="installed_apps",
    )

    class Meta:
        verbose_name = "Installed App"
        verbose_name_plural = "Installed Apps"
        ordering = ["gyro_name"]

    def __str__(self) -> str:
        return f"{self.gyro_name} v{self.version} [{self.state}]"
