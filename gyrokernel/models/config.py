"""System-wide configuration key-value store."""

from django.db import models

from .base import SoftDeleteModel, TimestampedModel, UUIDModel


class SystemParameter(UUIDModel, TimestampedModel, SoftDeleteModel):
    """
    Global key-value configuration accessible to all GyroERP apps.

    Convention: use dotted namespaced keys like 'gyrokernel.max_upload_mb'
    or 'accounting.default_currency'. Secrets are masked in API responses.
    Use the .get() / .set() class methods for safe access.
    """

    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_secret = models.BooleanField(
        default=False,
        help_text="When True, value is masked in API responses.",
    )

    class Meta:
        verbose_name = "System Parameter"
        verbose_name_plural = "System Parameters"
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Return parameter value for key, or default if not found / soft-deleted."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key: str, value: str, description: str = "") -> "SystemParameter":
        """Create or update a parameter and return the instance."""
        param, _ = cls.objects.update_or_create(
            key=key,
            defaults={"value": value, "description": description},
        )
        return param
