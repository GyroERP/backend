"""Tests for abstract base model behaviours via concrete kernel models."""

import uuid

import pytest

from gyrokernel.models import Company, Country, SystemParameter


@pytest.fixture
def us(db):
    return Country.objects.create(name="United States", code="US", alpha3="USA")


@pytest.mark.django_db
class TestUUIDModel:
    def test_pk_is_uuid(self, us):
        company = Company.objects.create(name="Test Corp", code="TC1", country=us)
        assert isinstance(company.id, uuid.UUID)

    def test_uuid_not_editable(self):
        field = Company._meta.get_field("id")
        assert field.editable is False

    def test_two_records_have_different_uuids(self, us):
        a = Company.objects.create(name="A", code="AAA", country=us)
        b = Company.objects.create(name="B", code="BBB", country=us)
        assert a.id != b.id


@pytest.mark.django_db
class TestTimestampedModel:
    def test_created_at_set_automatically(self, us):
        company = Company.objects.create(name="Acme", code="ACM", country=us)
        assert company.created_at is not None

    def test_updated_at_changes_on_save(self, us):
        company = Company.objects.create(name="Acme", code="ACM2", country=us)
        first_updated = company.updated_at
        company.name = "Acme Updated"
        company.save()
        assert company.updated_at >= first_updated


@pytest.mark.django_db
class TestSoftDeleteModel:
    def test_delete_sets_deleted_at_in_memory(self):
        param = SystemParameter.objects.create(key="sd.test", value="v")
        param.delete()
        assert param.deleted_at is not None

    def test_default_manager_excludes_deleted(self):
        SystemParameter.objects.create(key="visible", value="1")
        hidden = SystemParameter.objects.create(key="hidden", value="2")
        hidden.delete()

        keys = list(SystemParameter.objects.values_list("key", flat=True))
        assert "visible" in keys
        assert "hidden" not in keys

    def test_all_objects_includes_deleted(self):
        param = SystemParameter.objects.create(key="all.obj.test", value="x")
        param.delete()
        assert SystemParameter.all_objects.filter(key="all.obj.test").exists()

    def test_restore_clears_deleted_at(self):
        param = SystemParameter.objects.create(key="restore.me", value="v")
        param.delete()
        param.restore()
        assert param.deleted_at is None
        assert param.is_deleted is False
        assert SystemParameter.objects.filter(key="restore.me").exists()

    def test_hard_delete_removes_row(self):
        param = SystemParameter.objects.create(key="hard.del", value="v")
        param.hard_delete()
        assert not SystemParameter.all_objects.filter(key="hard.del").exists()

    def test_is_deleted_property(self):
        param = SystemParameter.objects.create(key="prop.test", value="v")
        assert param.is_deleted is False
        param.delete()
        assert param.is_deleted is True

    def test_queryset_bulk_delete_soft_deletes(self):
        SystemParameter.objects.create(key="bulk.a", value="1")
        SystemParameter.objects.create(key="bulk.b", value="2")
        SystemParameter.objects.filter(key__startswith="bulk.").delete()
        assert SystemParameter.objects.filter(key__startswith="bulk.").count() == 0
        assert SystemParameter.all_objects.filter(key__startswith="bulk.").count() == 2
