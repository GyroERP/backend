"""Company (tenant) model — the root of GyroERP multi-tenancy."""

from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class Company(UUIDModel, TimestampedModel, ActiveModel):
    """
    Represents an organisation or tenant in GyroERP.

    All business records are scoped to a Company via a ForeignKey.
    A Company can have subsidiaries through the parent FK, enabling
    multi-company holding structures.

    country, currency, state and language now reference proper master-data
    models instead of plain char codes, so validation and reporting are
    consistent across the whole ERP.
    """

    name = models.CharField(max_length=255)
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short unique identifier, e.g. 'ACME'",
    )

    # ---------- location / locale ----------
    country = models.ForeignKey(
        "gyrokernel.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    state = models.ForeignKey(
        "gyrokernel.CountryState",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    currency = models.ForeignKey(
        "gyrokernel.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    language = models.ForeignKey(
        "gyrokernel.Language",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    timezone = models.CharField(max_length=64, default="UTC")

    # ---------- address ----------
    street = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)

    # ---------- contact ----------
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    vat = models.CharField(max_length=50, blank=True, help_text="Tax / VAT registration number")

    # ---------- hierarchy ----------
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subsidiaries",
    )
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def is_subsidiary(self) -> bool:
        return self.parent_id is not None
