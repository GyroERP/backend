"""Country and CountryState models."""

from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class Country(UUIDModel, TimestampedModel, ActiveModel):
    """
    ISO 3166-1 country definition.

    Seeded via `python manage.py gyro_seed --only countries`.
    address_format is a multi-line template string where consumers
    can render postal addresses; left blank if no standard exists.
    """

    code = models.CharField(
        max_length=2,
        unique=True,
        help_text="ISO 3166-1 alpha-2 code, e.g. US",
    )
    name = models.CharField(max_length=100)
    alpha3 = models.CharField(max_length=3, blank=True, help_text="ISO 3166-1 alpha-3, e.g. USA")
    numeric_code = models.CharField(max_length=3, blank=True, help_text="ISO 3166-1 numeric, e.g. 840")
    phone_code = models.CharField(max_length=10, blank=True, help_text="Calling code, e.g. +1")
    address_format = models.TextField(
        blank=True,
        help_text="Postal address template using {street}, {city}, {zip}, {state}, {country}",
    )
    zip_required = models.BooleanField(default=False)
    state_required = models.BooleanField(default=False)
    vat_label = models.CharField(
        max_length=30,
        blank=True,
        default="VAT",
        help_text="Local label for the tax ID field, e.g. 'GST' in Australia",
    )
    currency = models.ForeignKey(
        "gyrokernel.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="countries",
        help_text="Default currency for this country",
    )

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class CountryState(UUIDModel, TimestampedModel):
    """
    ISO 3166-2 administrative subdivision (state / province / region).

    Seeded alongside Country via gyro_seed.
    """

    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="states",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text="Local state code, e.g. CA for California")

    class Meta:
        verbose_name = "Country State"
        verbose_name_plural = "Country States"
        ordering = ["country", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["country", "code"],
                name="unique_state_code_per_country",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
