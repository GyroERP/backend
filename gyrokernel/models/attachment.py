"""Attachment model — generic file storage with SHA-256 integrity."""

from __future__ import annotations

import hashlib
import os
import re

from django.conf import settings as django_settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .base import AuditModel, UUIDModel


# Characters that are safe in a stored filename. Everything else is stripped.
# This blocks path traversal (../), null bytes, shell metacharacters, etc.
# ISO 27001 A.14.2.5 — Secure development principles: validate all inputs.
_SAFE_FILENAME_RE = re.compile(r"[^\w.\-]")


def _sanitize_filename(filename: str) -> str:
    """
    Return a filename that is safe to use as a filesystem path component.

    Steps:
      1. Take only the basename (removes any directory components / path traversal).
      2. Replace every character that isn't alphanumeric, dot, hyphen, or
         underscore with an underscore.
      3. Strip leading dots to prevent hidden-file creation.
      4. Truncate to 200 chars so the full OS path stays under typical limits.
    """
    basename = os.path.basename(filename)
    safe = _SAFE_FILENAME_RE.sub("_", basename)
    safe = safe.lstrip(".")
    return safe[:200] or "unnamed"


def _attachment_upload_path(instance: "Attachment", filename: str) -> str:
    """Store under gyrokernel/attachments/<content_type_id>/<object_id>/<safe_filename>."""
    safe = _sanitize_filename(filename)
    return os.path.join(
        "gyrokernel",
        "attachments",
        str(instance.content_type_id or "orphan"),
        str(instance.object_id or "orphan"),
        safe,
    )


def _max_upload_bytes() -> int:
    """Return the configured max upload size in bytes (default 25 MB)."""
    mb = getattr(django_settings, "GYROERP_MAX_UPLOAD_SIZE_MB", 25)
    return mb * 1024 * 1024


class Attachment(UUIDModel, AuditModel):
    """
    File attached to any model via GenericForeignKey.

    checksum is computed on save so consumers can verify file integrity
    without re-downloading the file.  SHA-256 is chosen over MD5/SHA-1
    because it is collision-resistant and universally available.

    Filename is sanitized on upload to prevent path traversal.
    File size is validated against GYROERP_MAX_UPLOAD_SIZE_MB (default 25 MB).
    """

    name = models.CharField(max_length=255)

    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attachments",
    )
    object_id = models.CharField(max_length=36, blank=True, db_index=True)
    file_object = GenericForeignKey("content_type", "object_id")

    file = models.FileField(upload_to=_attachment_upload_path)
    file_size = models.PositiveIntegerField(default=0, editable=False)
    checksum = models.CharField(max_length=64, blank=True, editable=False, help_text="SHA-256 hex digest")
    mime_type = models.CharField(max_length=100, blank=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Attachment"
        verbose_name_plural = "Attachments"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, "read"):
            self._compute_file_metadata()
            self._validate_file_size()
        super().save(*args, **kwargs)

    def _compute_file_metadata(self) -> None:
        """Compute SHA-256 checksum and byte size from the in-memory file."""
        self.file.seek(0)
        sha = hashlib.sha256()
        total = 0
        for chunk in iter(lambda: self.file.read(8192), b""):
            sha.update(chunk)
            total += len(chunk)
        self.checksum = sha.hexdigest()
        self.file_size = total
        self.file.seek(0)

    def _validate_file_size(self) -> None:
        """Reject files exceeding GYROERP_MAX_UPLOAD_SIZE_MB. ISO 27001 A.13.1.1."""
        limit = _max_upload_bytes()
        if self.file_size > limit:
            limit_mb = limit // (1024 * 1024)
            raise ValidationError(
                f"File size {self.file_size:,} bytes exceeds the maximum allowed "
                f"upload size of {limit_mb} MB."
            )
