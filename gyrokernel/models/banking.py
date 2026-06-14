"""Bank and PartnerBank — banking information for partners."""

from __future__ import annotations

from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class Bank(UUIDModel, TimestampedModel, ActiveModel):
    """
    Financial institution registry.

    Partners can hold accounts at a named bank (with BIC/SWIFT) or at an
    unnamed bank (PartnerBank with bank=None).
    """

    name = models.CharField(max_length=255)
    bic = models.CharField(
        max_length=11,
        blank=True,
        help_text="SWIFT/BIC code, e.g. 'DEUTDEDB'",
    )
    country = models.ForeignKey(
        "gyrokernel.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="banks",
    )

    class Meta:
        verbose_name = "Bank"
        verbose_name_plural = "Banks"
        ordering = ["name"]

    def __str__(self) -> str:
        if self.bic:
            return f"{self.name} ({self.bic})"
        return self.name


class AccountType(models.TextChoices):
    IBAN = "iban", "IBAN"
    LOCAL = "local", "Local Account"
    OTHER = "other", "Other"


class PartnerBank(UUIDModel, TimestampedModel):
    """
    A bank account belonging to a partner.

    bank=None means the partner provided an account number but no bank
    details (e.g. a local cheque account).
    """

    partner = models.ForeignKey(
        "gyrokernel.Partner",
        on_delete=models.CASCADE,
        related_name="bank_accounts",
    )
    bank = models.ForeignKey(
        Bank,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="partner_accounts",
        help_text="Leave blank if bank details are unknown",
    )
    acc_number = models.CharField(
        max_length=100,
        help_text="IBAN or local account number",
    )
    acc_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
        default=AccountType.IBAN,
    )
    currency = models.ForeignKey(
        "gyrokernel.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Native currency of this account (informational)",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark as default payout account for this partner",
    )

    class Meta:
        verbose_name = "Partner Bank Account"
        verbose_name_plural = "Partner Bank Accounts"
        ordering = ["-is_primary", "acc_number"]

    def __str__(self) -> str:
        bank_label = str(self.bank) if self.bank_id else "Unknown bank"
        return f"{self.acc_number} @ {bank_label}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Enforce single primary per partner
            type(self).objects.filter(
                partner=self.partner,
                is_primary=True,
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
