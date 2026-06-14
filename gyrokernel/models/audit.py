"""Audit log — immutable record of every significant event in GyroERP."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .base import UUIDModel
from .company import Company


class AuditAction(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    LOGIN = "login", "Login"
    LOGOUT = "logout", "Logout"
    INSTALL = "install", "Install"
    UNINSTALL = "uninstall", "Uninstall"
    CUSTOM = "custom", "Custom"


class AuditLog(UUIDModel):
    """
    Immutable record of every significant action in the system.

    Never UPDATE or DELETE rows here — AuditLog is the compliance source of truth.
    Add new rows only; never modify existing ones.
    """

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    company = models.ForeignKey(
        Company,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=AuditAction.choices, db_index=True)
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.CharField(max_length=255, blank=True, db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    object_repr = models.CharField(max_length=500, blank=True)
    changes = models.JSONField(
        default=dict,
        help_text='{"field_name": [old_value, new_value]}',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    request_id = models.CharField(max_length=36, blank=True, db_index=True)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["company", "action"]),
        ]

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "?"
        return f"[{ts}] {self.action} by {self.user or 'system'}"
