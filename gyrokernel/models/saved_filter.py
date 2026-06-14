"""SavedFilter — persistent search filters per user/model."""

from __future__ import annotations

from django.conf import settings
from django.db import models

from .base import TimestampedModel, UUIDModel


class SavedFilter(UUIDModel, TimestampedModel):
    """
    A named, reusable search filter stored per user and model.

    Shares the same JSON domain format as RecordRule so DomainEvaluator
    can evaluate both interchangeably.

    is_default=True causes the filter to be applied automatically when a
    client opens the model's list view — only one default per (user, model) allowed.
    """

    name = models.CharField(max_length=200)
    model_name = models.CharField(
        max_length=150,
        db_index=True,
        help_text="App-qualified model label, e.g. 'sales.SalesOrder'",
    )
    domain = models.TextField(
        default="[]",
        help_text="JSON domain array — same format as RecordRule.domain",
    )
    context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extra context passed to the API when applying this filter",
    )
    sort = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ordering expression, e.g. '-created_at' or 'name,-amount'",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="saved_filters",
        help_text="Owner; null = shared across all users",
    )
    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="saved_filters",
        help_text="Scope to this company; null = all companies",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Auto-apply when opening model list; only one default per user+model",
    )

    class Meta:
        verbose_name = "Saved Filter"
        verbose_name_plural = "Saved Filters"
        ordering = ["model_name", "name"]

    def __str__(self) -> str:
        owner = str(self.user) if self.user_id else "shared"
        return f"{self.name} ({self.model_name}, {owner})"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Unset any existing default for the same user+model
            type(self).objects.filter(
                user=self.user,
                model_name=self.model_name,
                is_default=True,
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_defaults(cls, model_name: str, user=None, company=None):
        """Return the default filter(s) for a model+user combination."""
        qs = cls.objects.filter(model_name=model_name, is_default=True)
        if user is not None:
            qs = qs.filter(models.Q(user=user) | models.Q(user__isnull=True))
        if company is not None:
            qs = qs.filter(models.Q(company=company) | models.Q(company__isnull=True))
        return qs
