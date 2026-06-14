"""Partner model — universal contact directory (companies, individuals, vendors, customers)."""

from __future__ import annotations

import uuid as _uuid_mod

from django.db import models
from django.db.models import Value
from django.db.models.functions import Concat, Substr

from .base import GyroBaseModel, TimestampedModel, UUIDModel


class PartnerType(models.TextChoices):
    COMPANY = "company", "Company"
    INDIVIDUAL = "individual", "Individual"


class AddressType(models.TextChoices):
    CONTACT = "contact", "Contact"
    INVOICE = "invoice", "Invoice Address"
    DELIVERY = "delivery", "Delivery Address"
    OTHER = "other", "Other"


class PartnerTag(UUIDModel, TimestampedModel):
    """Free-form label that can be attached to any partner."""

    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, blank=True, default="")

    class Meta:
        verbose_name = "Partner Tag"
        verbose_name_plural = "Partner Tags"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Partner(GyroBaseModel):
    """
    Universal address/contact record with materialized path tree.

    Path format: "<pk_hex>/<child_pk_hex>/<grandchild_pk_hex>"
    Each segment is a UUID without hyphens (32 chars).  Separator is "/".

    - Root node:   path = pk.hex
    - Child node:  path = parent.path + "/" + pk.hex
    - Descendants: filter(path__startswith=self.path + "/")
    - Ancestors:   parse path segments, bulk-fetch by pk

    The path is recomputed on every save() and cascaded to all
    descendants if the parent changes (reparenting).
    """

    name = models.CharField(max_length=255)
    partner_type = models.CharField(
        max_length=15,
        choices=PartnerType.choices,
        default=PartnerType.COMPANY,
    )
    is_company = models.BooleanField(default=False)

    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="partners",
        help_text="Owning tenant; null means global/shared partner",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="contacts",
        help_text="Parent company partner for individual/address records",
    )
    address_type = models.CharField(
        max_length=10,
        choices=AddressType.choices,
        default=AddressType.CONTACT,
    )

    ref = models.CharField(max_length=50, blank=True, help_text="External reference / customer number")
    vat = models.CharField(max_length=50, blank=True, help_text="Tax / VAT registration number")

    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)

    street = models.CharField(max_length=255, blank=True)
    street2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    state = models.ForeignKey(
        "gyrokernel.CountryState",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    country = models.ForeignKey(
        "gyrokernel.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="partners",
    )
    language = models.ForeignKey(
        "gyrokernel.Language",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    timezone = models.CharField(max_length=64, default="UTC")

    tags = models.ManyToManyField(PartnerTag, blank=True, related_name="partners")
    notes = models.TextField(blank=True)

    # ------------------------------------------------------------------
    # Materialized path
    # ------------------------------------------------------------------
    path = models.CharField(
        max_length=4000,
        blank=True,
        db_index=True,
        editable=False,
        help_text="Materialized path — ancestor UUID hexes joined by '/', root first",
    )

    class Meta:
        verbose_name = "Partner"
        verbose_name_plural = "Partners"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    # ------------------------------------------------------------------
    # Save + path management
    # ------------------------------------------------------------------

    def save(self, *args, **kwargs):
        if self._state.adding:
            # For new records, super().save() first so self.pk is set (UUID assigned)
            super().save(*args, **kwargs)
            parent = type(self).all_objects.filter(pk=self.parent_id).first()
            self.path = f"{parent.path}/{self.pk.hex}" if parent else self.pk.hex
            type(self).all_objects.filter(pk=self.pk).update(path=self.path)
        else:
            old_path = self.path
            if self.parent_id:
                parent = type(self).all_objects.get(pk=self.parent_id)
                self.path = f"{parent.path}/{self.pk.hex}"
            else:
                self.path = self.pk.hex
            super().save(*args, **kwargs)
            if old_path and old_path != self.path:
                self._cascade_path_update(old_path, self.path)

    def _cascade_path_update(self, old_path: str, new_path: str) -> None:
        """Bulk-update the path prefix for every descendant after a reparent."""
        subtree = type(self).all_objects.filter(path__startswith=old_path + "/")
        # Substr is 1-indexed in Django; we want to keep everything after old_path
        suffix_pos = len(old_path) + 2  # skip old_path + "/"
        subtree.update(
            path=Concat(
                Value(new_path + "/"),
                Substr("path", suffix_pos),
            )
        )

    # ------------------------------------------------------------------
    # Tree traversal
    # ------------------------------------------------------------------

    @property
    def depth(self) -> int:
        """0 = root, 1 = first child, 2 = grandchild, etc."""
        if not self.path:
            return 0
        return self.path.count("/")

    @property
    def display_name(self) -> str:
        """
        Renders 'Company Name, Contact Name' for child contacts.
        Root companies and root individuals return just their name.
        """
        if self.parent_id and not self.is_company:
            return f"{self.parent.name}, {self.name}"
        return self.name

    def get_ancestors(self) -> list["Partner"]:
        """
        Return a list of ancestor partners ordered root → immediate parent.
        Excludes self.  Uses a single DB query (bulk fetch by pk).
        """
        if not self.path or "/" not in self.path:
            return []
        ancestor_hexes = self.path.split("/")[:-1]
        ancestor_pks = [_uuid_mod.UUID(h) for h in ancestor_hexes]
        by_pk = {
            str(p.pk): p
            for p in type(self).all_objects.filter(pk__in=ancestor_pks)
        }
        return [by_pk[str(_uuid_mod.UUID(h))] for h in ancestor_hexes if str(_uuid_mod.UUID(h)) in by_pk]

    def get_descendants(self):
        """
        Return QuerySet of ALL descendants (children, grandchildren, …).
        Excludes self.
        """
        if not self.path:
            return type(self).objects.none()
        return type(self).all_objects.filter(path__startswith=self.path + "/")

    def get_children(self):
        """Return QuerySet of direct children only (depth + 1)."""
        return type(self).all_objects.filter(parent=self)

    # ------------------------------------------------------------------
    # Commercial partner
    # ------------------------------------------------------------------

    @property
    def commercial_partner(self) -> "Partner":
        """
        Return the invoicing entity for this partner.

        Uses the materialized path for O(log n) ancestor lookup instead
        of the old recursive while-loop.
        """
        if self.is_company or not self.parent_id:
            return self
        ancestors = self.get_ancestors()
        # Walk from immediate parent backwards (reversed list) to find first company
        for ancestor in reversed(ancestors):
            if ancestor.is_company:
                return ancestor
        return self
