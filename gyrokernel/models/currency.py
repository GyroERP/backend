"""Currency and exchange rate models."""

from __future__ import annotations

import decimal
from datetime import date as date_type

from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class SymbolPosition(models.TextChoices):
    BEFORE = "before", "Before amount"
    AFTER = "after", "After amount"


class Currency(UUIDModel, TimestampedModel, ActiveModel):
    """
    ISO 4217 currency definition.

    Rates are stored in CurrencyRate as "1 unit of this currency = X USD".
    All arithmetic goes through round() to respect decimal_places.
    """

    iso_code = models.CharField(max_length=3, unique=True, help_text="ISO 4217 code, e.g. USD")
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, default="")
    symbol_position = models.CharField(
        max_length=6,
        choices=SymbolPosition.choices,
        default=SymbolPosition.BEFORE,
    )
    decimal_places = models.PositiveSmallIntegerField(default=2)
    rounding = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        default=decimal.Decimal("0.01"),
        help_text="Rounding unit, e.g. 0.01 for USD, 1.0 for JPY",
    )

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ["iso_code"]

    def __str__(self) -> str:
        return self.iso_code

    # ------------------------------------------------------------------
    # Arithmetic helpers
    # ------------------------------------------------------------------

    def round(self, amount: decimal.Decimal) -> decimal.Decimal:
        """Round amount to this currency's rounding unit using ROUND_HALF_UP."""
        if not self.rounding:
            return amount
        factor = decimal.Decimal(str(self.rounding))
        return (amount / factor).quantize(
            decimal.Decimal("1"), rounding=decimal.ROUND_HALF_UP
        ) * factor

    def is_zero(self, amount: decimal.Decimal) -> bool:
        return self.round(amount) == decimal.Decimal("0")

    def format_amount(self, amount: decimal.Decimal) -> str:
        """Return human-readable string like '$1,234.56' or '1.234,56 €'."""
        rounded = self.round(amount)
        formatted = f"{rounded:,.{self.decimal_places}f}"
        if self.symbol_position == SymbolPosition.BEFORE:
            return f"{self.symbol}{formatted}"
        return f"{formatted} {self.symbol}"

    def convert(
        self,
        amount: decimal.Decimal,
        to_currency: "Currency",
        company=None,
        date=None,
    ) -> decimal.Decimal:
        """
        Convert amount from this currency to to_currency.

        Rate model: 1 unit of currency = X USD (pivot).
        So: amount_in_to = amount * rate_from / rate_to
        """
        if self.pk == to_currency.pk:
            return to_currency.round(amount)

        rate_from = self._get_rate(company=company, date=date)
        rate_to = to_currency._get_rate(company=company, date=date)

        if not rate_from or not rate_to:
            raise ValueError(
                f"No exchange rate found for {self.iso_code} or {to_currency.iso_code}"
            )

        result = amount * rate_from / rate_to
        return to_currency.round(result)

    def _get_rate(self, company=None, date=None) -> decimal.Decimal | None:
        """Return the most recent rate on or before date (company-specific first)."""
        lookup_date = date or date_type.today()

        qs = CurrencyRate.objects.filter(
            currency=self,
            date__lte=lookup_date,
        ).order_by("-date")

        # Prefer company-specific rate
        if company is not None:
            company_rate = qs.filter(company=company).first()
            if company_rate:
                return company_rate.rate

        global_rate = qs.filter(company__isnull=True).first()
        return global_rate.rate if global_rate else None


class CurrencyRate(UUIDModel, TimestampedModel):
    """
    Exchange rate snapshot.

    rate = "1 unit of currency = X USD".
    company=None means global/default rate.
    """

    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="rates",
    )
    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="currency_rates",
    )
    rate = models.DecimalField(max_digits=22, decimal_places=6)
    date = models.DateField(db_index=True)

    class Meta:
        verbose_name = "Currency Rate"
        verbose_name_plural = "Currency Rates"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["currency", "company", "date"],
                name="unique_currency_rate_per_company_date",
            )
        ]

    def __str__(self) -> str:
        company_label = f" ({self.company})" if self.company_id else ""
        return f"{self.currency} = {self.rate} USD on {self.date}{company_label}"
