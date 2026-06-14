"""RecordRule — row-level access control via JSON domain expressions."""

from __future__ import annotations

import json

from django.contrib.auth.models import Group
from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class RecordRule(UUIDModel, TimestampedModel, ActiveModel):
    """
    Applies a domain filter to a model for specific groups.

    domain is a JSON array of triples: [["field", "op", "value"], ...]
    An empty groups set means the rule applies to every user.

    Usage:
        qs = RecordRule.apply_rules(MyModel.objects.all(), user, company)
    """

    name = models.CharField(max_length=200)
    model_name = models.CharField(
        max_length=100,
        help_text="Dotted model label, e.g. 'sales.SalesOrder'",
    )
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="record_rules",
        help_text="Restrict rule to these groups; empty = applies to all users",
    )
    domain = models.TextField(
        default="[]",
        help_text="JSON domain, e.g. [[\"company_id\",\"=\",\"@company_id\"]]",
    )
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=True)
    can_create = models.BooleanField(default=True)
    can_delete = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Record Rule"
        verbose_name_plural = "Record Rules"
        ordering = ["model_name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.model_name})"

    def get_domain(self) -> list:
        """Return parsed domain list (safe JSON load, never eval)."""
        try:
            return json.loads(self.domain)
        except (json.JSONDecodeError, TypeError):
            return []

    def apply(self, queryset, user, company=None):
        """
        Return queryset filtered by this rule's domain for the given user/company.

        Skips filtering if the rule's groups don't include this user.
        """
        from gyrokernel.domain import DomainEvaluator

        if self.groups.exists():
            user_group_ids = set(user.groups.values_list("id", flat=True))
            rule_group_ids = set(self.groups.values_list("id", flat=True))
            if not user_group_ids & rule_group_ids:
                return queryset

        domain = self.get_domain()
        if not domain:
            return queryset

        context = {
            "user_id": str(user.pk) if user else None,
            "company_id": str(company.pk) if company else None,
            "company_ids": [str(company.pk)] if company else [],
        }

        q = DomainEvaluator().to_q(domain, context=context)
        return queryset.filter(q)

    @classmethod
    def apply_rules(cls, queryset, user, company=None, model_name: str = ""):
        """Apply all active rules for the given model to the queryset."""
        if not model_name:
            opts = queryset.model._meta
            model_name = f"{opts.app_label}.{opts.object_name}"

        rules = cls.objects.filter(model_name=model_name, is_active=True)
        for rule in rules:
            queryset = rule.apply(queryset, user, company=company)
        return queryset
