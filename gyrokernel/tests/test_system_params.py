"""Tests for the SystemParameter model."""

import pytest

from gyrokernel.models import SystemParameter


@pytest.mark.django_db
class TestSystemParameter:
    def test_get_existing_key(self):
        SystemParameter.objects.create(key="gyrokernel.version", value="1.0.0")
        assert SystemParameter.get("gyrokernel.version") == "1.0.0"

    def test_get_returns_default_when_missing(self):
        assert SystemParameter.get("does.not.exist", default="fallback") == "fallback"

    def test_get_returns_empty_string_by_default(self):
        assert SystemParameter.get("also.missing") == ""

    def test_set_creates_new_param(self):
        param = SystemParameter.set("new.param", "hello")
        assert param.key == "new.param"
        assert param.value == "hello"
        assert SystemParameter.objects.filter(key="new.param").exists()

    def test_set_updates_existing_param(self):
        SystemParameter.objects.create(key="update.me", value="old")
        SystemParameter.set("update.me", "new")
        assert SystemParameter.get("update.me") == "new"

    def test_set_with_description(self):
        param = SystemParameter.set("described.param", "val", description="Some description")
        assert param.description == "Some description"

    def test_is_secret_flag(self):
        param = SystemParameter.objects.create(
            key="api.secret", value="s3cr3t", is_secret=True
        )
        assert param.is_secret is True
        assert param.value == "s3cr3t"

    def test_str_is_key(self):
        param = SystemParameter.objects.create(key="str.key", value="x")
        assert str(param) == "str.key"

    def test_soft_delete_hides_from_default_manager(self):
        SystemParameter.objects.create(key="sd.param", value="v")
        param = SystemParameter.objects.get(key="sd.param")
        param.delete()
        assert not SystemParameter.objects.filter(key="sd.param").exists()
        assert SystemParameter.all_objects.filter(key="sd.param").exists()

    def test_get_does_not_return_soft_deleted(self):
        SystemParameter.objects.create(key="deleted.param", value="gone")
        SystemParameter.objects.get(key="deleted.param").delete()
        assert SystemParameter.get("deleted.param", default="not found") == "not found"
