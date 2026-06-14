"""ModelPermission and GroupExtension — model-level ACL and group hierarchy."""

from __future__ import annotations

from collections import deque

from django.contrib.auth.models import Group
from django.db import models

from .base import ActiveModel, TimestampedModel, UUIDModel


class ModelPermission(UUIDModel, TimestampedModel, ActiveModel):
    """
    Model-level CRUD access control — answers "can group X access model Y at all?"

    Sits above RecordRule (row-level). A user denied at this level never reaches
    the row-level filter.  group=None means the permission applies to every
    authenticated user.
    """

    model_name = models.CharField(
        max_length=150,
        db_index=True,
        help_text="App-qualified model label, e.g. 'gyrokernel.Partner'",
    )
    group = models.ForeignKey(
        Group,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="model_permissions",
        help_text="Restrict to this group; null = applies to all authenticated users",
    )
    can_read = models.BooleanField(default=True)
    can_write = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Model Permission"
        verbose_name_plural = "Model Permissions"
        ordering = ["model_name", "group__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["model_name", "group"],
                name="unique_model_permission_per_group",
            )
        ]

    def __str__(self) -> str:
        group_label = self.group.name if self.group_id else "everyone"
        return f"{self.model_name} → {group_label}"

    @classmethod
    def check_access(
        cls,
        model_name: str,
        user,
        action: str,
    ) -> bool:
        """
        Return True if user is allowed to perform action on model_name.

        action: "read" | "write" | "create" | "delete"

        Evaluation order:
          1. Superusers always pass.
          2. Collect all ModelPermission rows matching model_name where group
             is null OR the user belongs to that group (including implied groups).
          3. If no matching rows exist → allow (open by default while permissions
             are being configured; set a deny-all global rule to lock down).
          4. Any matching row that grants the action → allow.
          5. Otherwise → deny.
        """
        if user.is_superuser:
            return True

        effective_group_ids = get_effective_group_ids(user)

        qs = cls.objects.filter(model_name=model_name, is_active=True).filter(
            models.Q(group__isnull=True) | models.Q(group_id__in=effective_group_ids)
        )
        rows = list(qs)
        if not rows:
            return True  # no rules configured → open

        field = f"can_{action}"
        return any(getattr(row, field) for row in rows)


class GroupExtension(UUIDModel, TimestampedModel):
    """
    ERP-enrichment sidecar for Django's auth.Group.

    Adds implied group hierarchy (transitive), category/ordering metadata,
    API key duration cap, and disjoint-group mutual exclusion.
    """

    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name="extension",
    )
    implied_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="implied_by",
        help_text="Groups transitively granted to members of this group",
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Logical category, e.g. 'Sales', 'Accounting', 'HR'",
    )
    sequence = models.IntegerField(
        default=10,
        help_text="Display order within the category (lower = first)",
    )
    max_key_duration_days = models.IntegerField(
        null=True,
        blank=True,
        help_text="Max API key lifetime in days for members; null = unlimited",
    )
    is_disjoint_with = models.ManyToManyField(
        "self",
        symmetrical=True,
        blank=True,
        help_text="Groups that cannot coexist with this one on the same user",
    )

    class Meta:
        verbose_name = "Group Extension"
        verbose_name_plural = "Group Extensions"
        ordering = ["category", "sequence", "group__name"]

    def __str__(self) -> str:
        return f"Extension({self.group.name})"

    def resolve_disjoint(self, user) -> list[Group]:
        """
        Return the list of groups that must be removed from user before
        assigning this group, based on is_disjoint_with relationships.
        """
        disjoint_ext_ids = self.is_disjoint_with.values_list("group_id", flat=True)
        return list(user.groups.filter(pk__in=disjoint_ext_ids))


# ---------------------------------------------------------------------------
# Module-level helpers (not methods so they can be imported without a model)
# ---------------------------------------------------------------------------

def get_effective_group_ids(user) -> set:
    """
    Return all group IDs that apply to user, including transitively implied groups.

    Uses BFS over GroupExtension.implied_groups to resolve the full set.
    """
    direct_ids = set(user.groups.values_list("id", flat=True))
    if not direct_ids:
        return direct_ids

    all_ids: set = set(direct_ids)
    queue: deque = deque(direct_ids)

    while queue:
        gid = queue.popleft()
        try:
            ext = GroupExtension.objects.get(group_id=gid)
        except GroupExtension.DoesNotExist:
            continue
        for implied in ext.implied_groups.all():
            if implied.pk not in all_ids:
                all_ids.add(implied.pk)
                queue.append(implied.pk)

    return all_ids


def get_effective_groups(user) -> list[Group]:
    """Return Group instances for all effective groups (direct + implied)."""
    ids = get_effective_group_ids(user)
    return list(Group.objects.filter(pk__in=ids))
