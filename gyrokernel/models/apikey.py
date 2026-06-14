"""APIKey — security-hardened programmatic authentication for GyroERP's API-first design."""

from __future__ import annotations

import ipaddress
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

from .base import TimestampedModel, UUIDModel


class APIKeyScope(models.TextChoices):
    FULL = "full", "Full Access"
    READ = "read", "Read Only (GET)"
    WRITE = "write", "Read + Write (no DELETE)"
    CUSTOM = "custom", "Custom Model List"


class APIKey(UUIDModel, TimestampedModel):
    """
    Programmatic authentication token.

    Wire format: gyro_<prefix8>_<hex40>
      - prefix  : first 8 chars of the 40-char hex, stored plain and indexed
                  for O(1) DB lookup — no timing exposure on the lookup itself
      - full key: verified via PBKDF2-SHA256 (Django make_password / check_password)
                  stored only as a hash, NEVER retrievable after creation

    Key lifecycle:
      generate() → returns (instance, raw_key) once; raw_key never stored
      authenticate(raw_key) → looks up by prefix, verifies hash, checks rules
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="api_keys",
    )
    name = models.CharField(
        max_length=200,
        help_text="Human label — e.g. 'CI pipeline', 'Mobile app v2'",
    )
    prefix = models.CharField(
        max_length=8,
        db_index=True,
        editable=False,
        help_text="First 8 hex chars of key — used for fast DB lookup",
    )
    hashed_key = models.CharField(
        max_length=256,
        editable=False,
        help_text="PBKDF2-SHA256 hash; the raw key is never stored",
    )
    scope = models.CharField(
        max_length=10,
        choices=APIKeyScope.choices,
        default=APIKeyScope.FULL,
    )
    allowed_models = models.JSONField(
        default=list,
        blank=True,
        help_text="For CUSTOM scope: allowed model labels e.g. ['sales.SalesOrder']",
    )
    ip_allowlist = models.JSONField(
        default=list,
        blank=True,
        help_text="CIDR blocks allowed to use this key; empty = any IP",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Hard expiry; null = governed by group max_key_duration_days",
    )
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    request_count = models.BigIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user} / {self.name} (gyro_{self.prefix}_…)"

    # ------------------------------------------------------------------
    # Key generation
    # ------------------------------------------------------------------

    @classmethod
    def generate(
        cls,
        user,
        name: str,
        scope: str = APIKeyScope.FULL,
        allowed_models: list | None = None,
        ip_allowlist: list | None = None,
        expires_at=None,
    ) -> tuple["APIKey", str]:
        """
        Create a new API key.

        Returns (instance, raw_key).  raw_key is shown ONCE — it cannot be
        retrieved afterward.  Validates group-level key duration caps.
        """
        if expires_at is not None:
            cls._validate_expiry(user, expires_at)

        # 160-bit random key
        raw_hex = secrets.token_bytes(20).hex()  # 40 hex chars
        prefix = raw_hex[:8]
        raw_key = f"gyro_{prefix}_{raw_hex}"

        instance = cls(
            user=user,
            name=name,
            prefix=prefix,
            hashed_key=make_password(raw_key),
            scope=scope,
            allowed_models=allowed_models or [],
            ip_allowlist=ip_allowlist or [],
            expires_at=expires_at,
        )
        instance.save()
        return instance, raw_key

    @classmethod
    def _validate_expiry(cls, user, expires_at) -> None:
        """Enforce group-level max_key_duration_days cap."""
        from .access_control import GroupExtension

        max_days = None
        for group in user.groups.all():
            try:
                ext = group.extension
            except GroupExtension.DoesNotExist:
                continue
            if ext.max_key_duration_days is not None:
                if max_days is None:
                    max_days = ext.max_key_duration_days
                else:
                    max_days = max(max_days, ext.max_key_duration_days)

        if max_days is not None:
            cap = timezone.now() + timedelta(days=max_days)
            if expires_at > cap:
                raise ValueError(
                    f"Your group allows a maximum API key lifetime of {max_days} days."
                )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @classmethod
    def authenticate(cls, raw_key: str, ip_address: str | None = None) -> "APIKey | None":
        """
        Validate a raw key string; return the APIKey instance or None.

        Steps:
          1. Parse wire format gyro_<prefix8>_<hex40>
          2. Query by prefix (indexed, no timing attack surface)
          3. Verify hash with PBKDF2 (constant-time via check_password)
          4. Check active, not expired, IP allowlist
          5. Record last_used_at/ip (deferred to caller to avoid blocking auth path)
        """
        if not raw_key or not raw_key.startswith("gyro_"):
            return None

        parts = raw_key.split("_", 2)
        if len(parts) != 3:
            return None
        _, prefix, _ = parts

        candidates = list(
            cls.objects.filter(prefix=prefix, is_active=True).select_related("user")
        )
        for candidate in candidates:
            if not check_password(raw_key, candidate.hashed_key):
                continue
            # Check expiry
            if candidate.expires_at and candidate.expires_at < timezone.now():
                return None
            # Check IP allowlist
            if ip_address and candidate.ip_allowlist:
                if not candidate._ip_allowed(ip_address):
                    return None
            return candidate
        return None

    def _ip_allowed(self, ip_address: str) -> bool:
        """Return True if ip_address falls within any CIDR in self.ip_allowlist."""
        try:
            addr = ipaddress.ip_address(ip_address)
        except ValueError:
            return False
        for cidr in self.ip_allowlist:
            try:
                if addr in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                continue
        return False

    def record_usage(self, ip_address: str | None = None) -> None:
        """Update usage metadata — call after successful authentication."""
        type(self).objects.filter(pk=self.pk).update(
            last_used_at=timezone.now(),
            last_used_ip=ip_address,
            request_count=models.F("request_count") + 1,
        )

    def deactivate(self, reason: str = "") -> None:
        self.is_active = False
        self.deactivated_at = timezone.now()
        self.deactivated_reason = reason
        self.save(update_fields=["is_active", "deactivated_at", "deactivated_reason"])

    # ------------------------------------------------------------------
    # Scope helpers
    # ------------------------------------------------------------------

    def allows_method(self, http_method: str) -> bool:
        """Return True if this key's scope permits the given HTTP method."""
        method = http_method.upper()
        if self.scope == APIKeyScope.FULL:
            return True
        if self.scope == APIKeyScope.READ:
            return method == "GET"
        if self.scope == APIKeyScope.WRITE:
            return method in {"GET", "POST", "PUT", "PATCH"}
        # CUSTOM — method not restricted at key level, checked at model level
        return True

    def allows_model(self, model_name: str) -> bool:
        """For CUSTOM scope: check if model_name is in allowed_models."""
        if self.scope != APIKeyScope.CUSTOM:
            return True
        return model_name in (self.allowed_models or [])

    @property
    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at < timezone.now())
