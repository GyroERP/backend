"""Abstract base models shared across all GyroERP apps."""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    """Replaces the integer PK with a UUID — no sequential enumeration, distributed-safe."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """Adds automatic created_at and updated_at timestamps."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class AuditModel(TimestampedModel):
    """Extends TimestampedModel with who-created / who-last-updated tracking."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        db_column="created_by_id",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        db_column="updated_by_id",
    )

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that understands soft-deleted rows."""

    def delete(self):
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Default manager — excludes soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Secondary manager — includes soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    """
    Marks rows as deleted rather than removing them from the database.

    Use .delete() for soft deletion and .hard_delete() to permanently remove.
    The default objects manager filters out soft-deleted rows automatically;
    use .all_objects to see everything including deleted rows.
    """

    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        db_column="deleted_by_id",
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    def delete(self, using=None, keep_parents=False, deleted_by=None):  # type: ignore[override]
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """Adds a simple is_active flag for enabling / disabling records."""

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class GyroBaseModel(UUIDModel, AuditModel, SoftDeleteModel, ActiveModel):
    """
    Canonical abstract base for GyroERP business objects.

    Provides: UUID PK · timestamps · created_by/updated_by · soft-delete · is_active.
    Business app models should inherit this class.
    """

    class Meta:
        abstract = True
        ordering = ["-created_at"]
