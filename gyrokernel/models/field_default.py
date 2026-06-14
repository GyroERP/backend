"""FieldDefault — per-user / per-company default values stored in the database."""

from __future__ import annotations

import json

from django.conf import settings
from django.db import models

from .base import TimestampedModel, UUIDModel


class FieldDefault(UUIDModel, TimestampedModel):
    """
    Database-stored default value for a model field.

    Specificity ladder (most specific wins):
      user + company  >  user only  >  company only  >  global (both null)

    json_value stores a JSON-encoded Python value (string, int, list, dict, etc.)
    so that heterogeneous field types are supported without separate columns.

    Example usage:
        # Set default warehouse for a user in company X:
        FieldDefault.set("inventory.StockMove", "warehouse_id", str(wh.pk),
                         user=request.user, company=request.company)

        # Read it back:
        warehouse_id = FieldDefault.get("inventory.StockMove", "warehouse_id",
                                         user=request.user, company=request.company)
    """

    model_name = models.CharField(
        max_length=150,
        db_index=True,
        help_text="App-qualified model label, e.g. 'sales.SalesOrder'",
    )
    field_name = models.CharField(max_length=100, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="field_defaults",
        help_text="Specific user; null = applies to all users",
    )
    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="field_defaults",
        help_text="Specific company; null = applies to all companies",
    )
    json_value = models.TextField(
        help_text="JSON-encoded default value",
    )

    class Meta:
        verbose_name = "Field Default"
        verbose_name_plural = "Field Defaults"
        ordering = ["model_name", "field_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["model_name", "field_name", "user", "company"],
                name="unique_field_default_per_scope",
            )
        ]

    def __str__(self) -> str:
        scope = []
        if self.user_id:
            scope.append(f"user={self.user_id}")
        if self.company_id:
            scope.append(f"company={self.company_id}")
        scope_label = ", ".join(scope) if scope else "global"
        return f"{self.model_name}.{self.field_name} [{scope_label}]"

    @property
    def value(self):
        """Return the decoded Python value."""
        return json.loads(self.json_value)

    @value.setter
    def value(self, v) -> None:
        self.json_value = json.dumps(v)

    # ------------------------------------------------------------------
    # Class-level helpers
    # ------------------------------------------------------------------

    @classmethod
    def get(
        cls,
        model_name: str,
        field_name: str,
        user=None,
        company=None,
        default=None,
    ):
        """
        Return the most-specific default value, or `default` if none is set.

        Specificity (highest to lowest):
          user + company → user only → company only → global
        """
        qs = cls.objects.filter(model_name=model_name, field_name=field_name)

        candidates = [
            qs.filter(user=user, company=company).first() if user and company else None,
            qs.filter(user=user, company__isnull=True).first() if user else None,
            qs.filter(user__isnull=True, company=company).first() if company else None,
            qs.filter(user__isnull=True, company__isnull=True).first(),
        ]
        for candidate in candidates:
            if candidate is not None:
                return candidate.value
        return default

    @classmethod
    def set(
        cls,
        model_name: str,
        field_name: str,
        value,
        user=None,
        company=None,
    ) -> "FieldDefault":
        """Create or update the default for the given scope."""
        instance, _ = cls.objects.update_or_create(
            model_name=model_name,
            field_name=field_name,
            user=user,
            company=company,
            defaults={"json_value": json.dumps(value)},
        )
        return instance

    @classmethod
    def clear(
        cls,
        model_name: str,
        field_name: str,
        user=None,
        company=None,
    ) -> int:
        """Remove the default for the given scope. Returns number of rows deleted."""
        return cls.objects.filter(
            model_name=model_name,
            field_name=field_name,
            user=user,
            company=company,
        ).delete()[0]
