"""Tests for ModelPermission and GroupExtension."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from gyrokernel.models import GroupExtension, ModelPermission
from gyrokernel.models.access_control import get_effective_group_ids

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="tester", password="pass")


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(username="admin", password="pass")


@pytest.fixture
def group(db):
    return Group.objects.create(name="Sales User")


@pytest.mark.django_db
class TestModelPermission:
    def test_no_rules_open_by_default(self, user):
        assert ModelPermission.check_access("sales.SalesOrder", user, "read") is True

    def test_superuser_always_passes(self, superuser):
        ModelPermission.objects.create(
            model_name="sales.SalesOrder",
            group=None,
            can_read=False,
        )
        assert ModelPermission.check_access("sales.SalesOrder", superuser, "read") is True

    def test_global_rule_grants_read(self, user):
        ModelPermission.objects.create(
            model_name="sales.SalesOrder",
            group=None,
            can_read=True,
            can_write=False,
        )
        assert ModelPermission.check_access("sales.SalesOrder", user, "read") is True
        assert ModelPermission.check_access("sales.SalesOrder", user, "write") is False

    def test_group_rule_applies_when_user_in_group(self, user, group):
        user.groups.add(group)
        ModelPermission.objects.create(
            model_name="gyrokernel.Partner",
            group=group,
            can_read=True,
            can_create=True,
        )
        assert ModelPermission.check_access("gyrokernel.Partner", user, "read") is True
        assert ModelPermission.check_access("gyrokernel.Partner", user, "create") is True
        assert ModelPermission.check_access("gyrokernel.Partner", user, "delete") is False

    def test_group_rule_skipped_when_user_not_in_group(self, user, group):
        ModelPermission.objects.create(
            model_name="gyrokernel.Partner",
            group=group,
            can_read=True,
        )
        # User is NOT in group; no global rule either → open-by-default (no matching rows)
        # Wait — there IS a row but the user doesn't match it...
        # The row's group doesn't match user's groups, so it isn't in qs → no rows → allow
        assert ModelPermission.check_access("gyrokernel.Partner", user, "read") is True

    def test_inactive_rule_ignored(self, user):
        ModelPermission.objects.create(
            model_name="sales.SalesOrder",
            group=None,
            can_read=False,
            is_active=False,
        )
        assert ModelPermission.check_access("sales.SalesOrder", user, "read") is True

    def test_str_representation(self, group):
        mp = ModelPermission(model_name="sales.SalesOrder", group=group)
        assert "sales.SalesOrder" in str(mp)
        assert "Sales User" in str(mp)


@pytest.mark.django_db
class TestGroupExtension:
    def test_implied_groups_expanded(self, user):
        parent = Group.objects.create(name="Sales Manager")
        child = Group.objects.create(name="Sales User")

        ext = GroupExtension.objects.create(group=parent)
        ext.implied_groups.add(child)

        user.groups.add(parent)

        effective_ids = get_effective_group_ids(user)
        assert parent.pk in effective_ids
        assert child.pk in effective_ids

    def test_transitive_implied_groups(self, user):
        g1 = Group.objects.create(name="Admin")
        g2 = Group.objects.create(name="Manager")
        g3 = Group.objects.create(name="User")

        ext1 = GroupExtension.objects.create(group=g1)
        ext1.implied_groups.add(g2)
        ext2 = GroupExtension.objects.create(group=g2)
        ext2.implied_groups.add(g3)

        user.groups.add(g1)

        effective_ids = get_effective_group_ids(user)
        assert g1.pk in effective_ids
        assert g2.pk in effective_ids
        assert g3.pk in effective_ids

    def test_user_with_no_groups_returns_empty_set(self, user):
        ids = get_effective_group_ids(user)
        assert ids == set()

    def test_resolve_disjoint_returns_conflicting_groups(self, user):
        g1 = Group.objects.create(name="Sales User")
        g2 = Group.objects.create(name="Sales Manager")

        ext1 = GroupExtension.objects.create(group=g1)
        ext2 = GroupExtension.objects.create(group=g2)
        ext1.is_disjoint_with.add(ext2)

        user.groups.add(g1)

        to_remove = ext2.resolve_disjoint(user)
        assert g1 in to_remove

    def test_str_representation(self):
        group = Group.objects.create(name="Test Group")
        ext = GroupExtension.objects.create(group=group)
        assert "Test Group" in str(ext)
