"""Attachment model — generic file storage with SHA-256 integrity."""

from __future__ import annotations

import hashlib
import os

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .base import AuditModel, UUIDModel


def _attachment_upload_path(instance: "Attachment", filename: str) -> str:
    """Store under gyrokernel/attachments/<content_type_id>/<object_id>/<filename>."""
    return os.path.join(
        "gyrokernel",
        "attachments",
        str(instance.content_type_id or "orphan"),
        str(instance.object_id or "orphan"),
        filename,
    )


class Attachment(UUIDModel, AuditModel):
    """
    File attached to any model via GenericForeignKey.

    checksum is computed on save so consumers can verify file integrity
    without re-downloading the file.  SHA-256 is chosen over MD5/SHA-1
    because it is collision-resistant and universally available.
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
