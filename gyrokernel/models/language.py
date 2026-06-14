"""Language and locale model."""

from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class TextDirection(models.TextChoices):
    LTR = "ltr", "Left to Right"
    RTL = "rtl", "Right to Left"


class Language(UUIDModel, TimestampedModel, ActiveModel):
    """
    Locale-aware language definition.

    code uses the ll_CC convention (language_COUNTRY), e.g. "en_US", "ar_SA".
    direction drives RTL layout in frontends; the kernel stores it so any
    consumer (web, mobile, PDF renderer) can respect it without hardcoding.
    """

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Locale code, e.g. en_US, ar_SA",
    )
    name = models.CharField(max_length=100, help_text="English display name")
    iso_code = models.CharField(
        max_length=5,
        help_text="ISO 639-1 language code, e.g. en, ar",
    )
    url_code = models.CharField(
        max_length=10,
        blank=True,
        help_text="URL path segment, e.g. 'en' or 'ar'",
    )
    direction = models.CharField(
        max_length=3,
        choices=TextDirection.choices,
        default=TextDirection.LTR,
    )
    date_format = models.CharField(
        max_length=30,
        default="%m/%d/%Y",
        help_text="Python strftime format for dates",
    )
    time_format = models.CharField(
        max_length=30,
        default="%H:%M:%S",
        help_text="Python strftime format for times",
    )
    decimal_point = models.CharField(max_length=1, default=".")
    thousands_separator = models.CharField(max_length=1, default=",")
    week_start = models.PositiveSmallIntegerField(
        default=0,
        help_text="0=Monday … 6=Sunday",
    )

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    @property
    def is_rtl(self) -> bool:
        return self.direction == TextDirection.RTL
