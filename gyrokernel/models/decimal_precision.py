"""DecimalPrecision — configurable decimal places per use-case, stored in the database."""

from __future__ import annotations

from django.db import models

from .base import TimestampedModel, UUIDModel


class DecimalPrecision(UUIDModel, TimestampedModel):
    """
    Named decimal precision configuration.

    Business apps register a precision name (e.g. "Product Price", "Discount")
    and retrieve the configured digit count at runtime.  Per-company overrides
    allow different precision for subsidiaries.

    Usage:
        dp = DecimalPrecision.get_digits("Product Price", company=request.company)
        # dp == 2 by default, 4 if company configured it
    """

    name = models.CharField(
        max_length=100,
        help_text="Precision identifier, e.g. 'Product Price', 'Unit of Measure'",
    )
    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="decimal_precisions",
        help_text="Company-specific override; null = global default",
    )
    digits = models.PositiveSmallIntegerField(
        default=2,
        help_text="Number of decimal places",
    )

    class Meta:
        verbose_name = "Decimal Precision"
        verbose_name_plural = "Decimal Precisions"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "company"],
                name="unique_decimal_precision_per_company",
            )
        ]

    def __str__(self) -> str:
        company_label = f" ({self.company})" if self.company_id else ""
        return f"{self.name}{company_label}: {self.digits} dp"

    @classmethod
    def get_digits(cls, name: str, company=None, default: int = 2) -> int:
        """
        Return digit count for a named precision.

        Company-specific row takes priority over global (company=None) row.
        Falls back to `default` if neither is found.
        """
        if company is not None:
            row = cls.objects.filter(name=name, company=company).first()
            if row:
                return row.digits

        global_row = cls.objects.filter(name=name, company__isnull=True).first()
        return global_row.digits if global_row else default

    @classmethod
    def ensure(cls, name: str, digits: int = 2) -> "DecimalPrecision":
        """
        Get-or-create the global (company=None) precision row.
        Used in data migrations and seeding.
        """
        row, _ = cls.objects.get_or_create(
            name=name,
            company=None,
            defaults={"digits": digits},
        )
        return row
