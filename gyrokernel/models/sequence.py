"""Sequence model — gap-free, date-range-aware document numbering."""

from __future__ import annotations

import re
from datetime import date as date_type

from django.db import models, transaction

from .base import ActiveModel, TimestampedModel, UUIDModel

_PLACEHOLDER_RE = re.compile(r"\{(year|month|day)\}")


def _interpolate(template: str, d: date_type) -> str:
    """Replace {year}, {month}, {day} in template with zero-padded date parts."""
    return _PLACEHOLDER_RE.sub(
        lambda m: {
            "year": str(d.year),
            "month": f"{d.month:02d}",
            "day": f"{d.day:02d}",
        }[m.group(1)],
        template,
    )


class SequenceImplementation(models.TextChoices):
    STANDARD = "standard", "Standard (may have gaps)"
    NO_GAP = "no_gap", "No Gap (SELECT FOR UPDATE)"


class Sequence(UUIDModel, TimestampedModel, ActiveModel):
    """
    Named counter that produces formatted document numbers.

    prefix/suffix support {year}, {month}, {day} interpolation.
    Example: prefix="INV/{year}/{month}/", padding=4 →  "INV/2024/06/0001"

    For NO_GAP mode the entire next() call runs inside select_for_update()
    so concurrent transactions block rather than skip a number.
    """

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    prefix = models.CharField(max_length=50, blank=True)
    suffix = models.CharField(max_length=50, blank=True)
    padding = models.PositiveIntegerField(default=4)
    step = models.PositiveIntegerField(default=1)
    implementation = models.CharField(
        max_length=10,
        choices=SequenceImplementation.choices,
        default=SequenceImplementation.STANDARD,
    )
    use_date_range = models.BooleanField(
        default=False,
        help_text="Reset counter at the start of each year",
    )
    next_number = models.PositiveIntegerField(
        default=1,
        help_text="Next counter value when use_date_range=False",
    )

    class Meta:
        verbose_name = "Sequence"
        verbose_name_plural = "Sequences"
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def next_by_code(cls, code: str, date: date_type | None = None) -> str:
        """
        Return the next formatted sequence value for the given code.

        Thread-safe: uses SELECT FOR UPDATE for no-gap sequences.
        Caller must be inside a transaction for the lock to be meaningful.
        """
        from django.utils import timezone

        use_date = date or timezone.now().date()

        with transaction.atomic():
            seq = (
                cls.objects.select_for_update()
                .filter(code=code, is_active=True)
                .first()
            )
            if seq is None:
                raise ValueError(f"No active sequence found with code='{code}'")
            return seq._next(use_date)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _next(self, d: date_type) -> str:
        if self.use_date_range:
            return self._next_with_date_range(d)
        return self._advance_and_format(d, self.next_number)

    def _next_with_date_range(self, d: date_type) -> str:
        year_start = date_type(d.year, 1, 1)
        year_end = date_type(d.year, 12, 31)

        dr, created = SequenceDateRange.objects.select_for_update().get_or_create(
            sequence=self,
            date_from=year_start,
            defaults={"date_to": year_end, "next_number": 1},
        )
        number = dr.next_number
        dr.next_number += self.step
        dr.save(update_fields=["next_number"])
        return self._format(d, number)

    def _advance_and_format(self, d: date_type, number: int) -> str:
        self.next_number += self.step
        self.save(update_fields=["next_number"])
        return self._format(d, number)

    def _format(self, d: date_type, number: int) -> str:
        prefix = _interpolate(self.prefix, d)
        suffix = _interpolate(self.suffix, d)
        counter = str(number).zfill(self.padding)
        return f"{prefix}{counter}{suffix}"


class SequenceDateRange(UUIDModel, TimestampedModel):
    """
    Per-year counter bucket for a Sequence with use_date_range=True.

    date_from is always Jan 1 of the year; date_to is Dec 31.
    """

    sequence = models.ForeignKey(
        Sequence,
        on_delete=models.CASCADE,
        related_name="date_ranges",
    )
    date_from = models.DateField()
    date_to = models.DateField(null=True, blank=True)
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Sequence Date Range"
        verbose_name_plural = "Sequence Date Ranges"
        ordering = ["sequence", "-date_from"]
        constraints = [
            models.UniqueConstraint(
                fields=["sequence", "date_from"],
                name="unique_sequence_date_range",
            )
        ]

    def __str__(self) -> str:
        return f"{self.sequence.code} from {self.date_from}"
