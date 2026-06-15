"""MailServer — outgoing SMTP configuration per company."""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel

logger = logging.getLogger(__name__)


class MailEncryption(models.TextChoices):
    NONE = "none", "None (plain)"
    STARTTLS = "starttls", "STARTTLS"
    SSL = "ssl", "SSL/TLS"


class MailServer(UUIDModel, TimestampedModel, ActiveModel):
    """
    Outgoing SMTP server configuration.

    Supports multi-server setups: different servers per company, per from-domain,
    or a global fallback.  pick() selects the best match; send() delivers the mail.

    SMTP password storage:
      - Production (DEBUG=False): Fernet (AES-256) is REQUIRED.
        Set GYROERP_FERNET_KEY env var or the server will refuse to save a password.
      - Development (DEBUG=True): falls back to plain-text storage with a log warning.

    ISO 27001 A.10.1.1 — Encryption must be used for sensitive data at rest.
    """

    name = models.CharField(max_length=200)
    company = models.ForeignKey(
        "gyrokernel.Company",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mail_servers",
        help_text="Restrict to this company; null = global default",
    )
    smtp_host = models.CharField(max_length=255, default="localhost")
    smtp_port = models.IntegerField(default=587)
    smtp_encryption = models.CharField(
        max_length=10,
        choices=MailEncryption.choices,
        default=MailEncryption.STARTTLS,
    )
    smtp_user = models.CharField(max_length=255, blank=True)
    smtp_password = models.CharField(
        max_length=1024,
        blank=True,
        help_text="Stored AES-256 encrypted (requires GYROERP_FERNET_KEY in production)",
    )
    from_filter = models.CharField(
        max_length=255,
        blank=True,
        help_text="Use this server only for 'from' addresses matching this domain/address",
    )
    sequence = models.IntegerField(
        default=10,
        help_text="Priority when multiple servers match (lower = higher priority)",
    )
    debug_mode = models.BooleanField(
        default=False,
        help_text="Log raw SMTP conversation — MUST NOT be enabled in production",
    )

    class Meta:
        verbose_name = "Mail Server"
        verbose_name_plural = "Mail Servers"
        ordering = ["sequence", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.smtp_host}:{self.smtp_port})"

    def clean(self):
        # debug_mode logs the raw SMTP conversation, which includes credentials.
        # Block it entirely in non-DEBUG environments.  ISO 27001 A.12.4.1.
        if self.debug_mode and not getattr(django_settings, "DEBUG", False):
            raise ValidationError(
                {"debug_mode": "debug_mode must not be enabled in production (DEBUG=False)."}
            )

    # ------------------------------------------------------------------
    # Password encryption helpers
    # ------------------------------------------------------------------

    def set_password(self, plain_password: str) -> None:
        """Encrypt and store the SMTP password."""
        fernet = self._get_fernet()
        if fernet:
            self.smtp_password = fernet.encrypt(plain_password.encode()).decode()
        else:
            # In production, refuse to store passwords in plain text.
            if not getattr(django_settings, "DEBUG", False):
                raise ImproperlyConfigured(
                    "GYROERP_FERNET_KEY must be set in production to encrypt SMTP passwords. "
                    "Generate one with: python -c \"from cryptography.fernet import Fernet; "
                    "print(Fernet.generate_key().decode())\""
                )
            logger.warning(
                "GYROERP_FERNET_KEY not set — SMTP password stored in plain text. "
                "This is acceptable in development but MUST NOT reach production."
            )
            self.smtp_password = plain_password

    def get_password(self) -> str:
        """Decrypt and return the SMTP password."""
        fernet = self._get_fernet()
        if fernet and self.smtp_password:
            try:
                return fernet.decrypt(self.smtp_password.encode()).decode()
            except Exception:
                # If decryption fails the value may be an un-encrypted legacy entry.
                # Log and return as-is so existing rows don't silently break.
                logger.error(
                    "Failed to decrypt SMTP password for server '%s'. "
                    "The stored value may be corrupt or was stored without encryption.",
                    self.name,
                )
                return self.smtp_password
        return self.smtp_password

    @staticmethod
    def _get_fernet():
        """Return a Fernet instance if GYROERP_FERNET_KEY is configured, else None."""
        key = getattr(django_settings, "GYROERP_FERNET_KEY", None)
        if not key:
            return None
        try:
            from cryptography.fernet import Fernet

            return Fernet(key.encode() if isinstance(key, str) else key)
        except ImportError:
            raise ImproperlyConfigured(
                "The 'cryptography' package is required for SMTP password encryption. "
                "Install it with: pip install cryptography"
            )

    # ------------------------------------------------------------------
    # Server selection
    # ------------------------------------------------------------------

    @classmethod
    def pick(cls, from_address: str = "", company=None) -> "MailServer | None":
        """
        Return the best MailServer for the given from_address + company.

        Priority (highest first):
          1. Company-specific + from_filter matches
          2. Company-specific + no from_filter
          3. Global + from_filter matches
          4. Global + no from_filter
        """
        qs = cls.objects.filter(is_active=True).order_by("sequence")

        def _match(server: "MailServer") -> bool:
            if server.from_filter:
                return (
                    from_address.endswith("@" + server.from_filter)
                    or from_address == server.from_filter
                )
            return True

        candidates: list["MailServer"] = []
        # Company-specific first
        if company is not None:
            candidates += [s for s in qs.filter(company=company) if _match(s)]
        # Global fallback
        candidates += [s for s in qs.filter(company__isnull=True) if _match(s)]
        return candidates[0] if candidates else None

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send(self, message: EmailMessage) -> None:
        """Deliver an email.message.EmailMessage via this SMTP server."""
        if self.debug_mode and not getattr(django_settings, "DEBUG", False):
            raise RuntimeError(
                "debug_mode is enabled on mail server '%s' but DEBUG=False. "
                "Disable debug_mode before sending." % self.name
            )

        password = self.get_password()
        context = ssl.create_default_context()

        if self.smtp_encryption == MailEncryption.SSL:
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as conn:
                if self.debug_mode:
                    conn.set_debuglevel(1)
                if self.smtp_user:
                    conn.login(self.smtp_user, password)
                conn.send_message(message)
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as conn:
                if self.debug_mode:
                    conn.set_debuglevel(1)
                if self.smtp_encryption == MailEncryption.STARTTLS:
                    conn.starttls(context=context)
                if self.smtp_user:
                    conn.login(self.smtp_user, password)
                conn.send_message(message)

    @classmethod
    def send_mail(
        cls,
        message: EmailMessage,
        from_address: str = "",
        company=None,
    ) -> bool:
        """
        Pick the best server and deliver the message.
        Returns True on success, False if no server is configured.
        """
        server = cls.pick(from_address=from_address, company=company)
        if not server:
            logger.warning("No outgoing mail server configured; email not sent")
            return False
        server.send(message)
        return True
