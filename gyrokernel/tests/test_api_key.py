"""Tests for APIKey model — generation, authentication, scope, expiry, IP allowlist."""

import pytest
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from gyrokernel.models import APIKey, APIKeyScope

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass")


@pytest.mark.django_db
class TestAPIKeyGenerate:
    def test_generate_returns_instance_and_raw_key(self, user):
        instance, raw_key = APIKey.generate(user, name="CI pipeline")
        assert instance.pk is not None
        assert raw_key.startswith("gyro_")
        assert len(raw_key) == 5 + 8 + 1 + 40  # "gyro_" + prefix + "_" + hex40

    def test_prefix_stored_plain(self, user):
        instance, raw_key = APIKey.generate(user, name="test")
        expected_prefix = raw_key[5:13]  # chars after "gyro_"
        assert instance.prefix == expected_prefix

    def test_raw_key_never_stored(self, user):
        instance, raw_key = APIKey.generate(user, name="test")
        assert instance.hashed_key != raw_key
        assert not instance.hashed_key.startswith("gyro_")

    def test_two_keys_have_different_raw_keys(self, user):
        _, key1 = APIKey.generate(user, name="key1")
        _, key2 = APIKey.generate(user, name="key2")
        assert key1 != key2

    def test_default_scope_is_full(self, user):
        instance, _ = APIKey.generate(user, name="test")
        assert instance.scope == APIKeyScope.FULL

    def test_custom_scope_stored(self, user):
        instance, _ = APIKey.generate(user, name="test", scope=APIKeyScope.READ)
        assert instance.scope == APIKeyScope.READ

    def test_ip_allowlist_stored(self, user):
        instance, _ = APIKey.generate(user, name="test", ip_allowlist=["10.0.0.0/8"])
        assert "10.0.0.0/8" in instance.ip_allowlist

    def test_expires_at_stored(self, user):
        expires = timezone.now() + timedelta(days=30)
        instance, _ = APIKey.generate(user, name="test", expires_at=expires)
        assert instance.expires_at is not None


@pytest.mark.django_db
class TestAPIKeyAuthenticate:
    def test_valid_key_authenticates(self, user):
        instance, raw_key = APIKey.generate(user, name="test")
        result = APIKey.authenticate(raw_key)
        assert result is not None
        assert result.pk == instance.pk

    def test_invalid_key_returns_none(self, user):
        APIKey.generate(user, name="test")
        result = APIKey.authenticate("gyro_badprefx_" + "a" * 40)
        assert result is None

    def test_wrong_format_returns_none(self):
        assert APIKey.authenticate("Bearer some_token") is None
        assert APIKey.authenticate("") is None
        assert APIKey.authenticate(None) is None

    def test_inactive_key_not_authenticated(self, user):
        instance, raw_key = APIKey.generate(user, name="test")
        instance.deactivate()
        result = APIKey.authenticate(raw_key)
        assert result is None

    def test_expired_key_not_authenticated(self, user):
        past = timezone.now() - timedelta(seconds=1)
        instance, raw_key = APIKey.generate(user, name="test", expires_at=past)
        result = APIKey.authenticate(raw_key)
        assert result is None

    def test_not_expired_key_authenticates(self, user):
        future = timezone.now() + timedelta(days=30)
        _, raw_key = APIKey.generate(user, name="test", expires_at=future)
        result = APIKey.authenticate(raw_key)
        assert result is not None

    def test_ip_allowlist_blocks_disallowed_ip(self, user):
        _, raw_key = APIKey.generate(user, name="test", ip_allowlist=["192.168.1.0/24"])
        result = APIKey.authenticate(raw_key, ip_address="10.0.0.1")
        assert result is None

    def test_ip_allowlist_allows_matching_ip(self, user):
        _, raw_key = APIKey.generate(user, name="test", ip_allowlist=["192.168.1.0/24"])
        result = APIKey.authenticate(raw_key, ip_address="192.168.1.50")
        assert result is not None

    def test_empty_allowlist_allows_any_ip(self, user):
        _, raw_key = APIKey.generate(user, name="test", ip_allowlist=[])
        result = APIKey.authenticate(raw_key, ip_address="1.2.3.4")
        assert result is not None


@pytest.mark.django_db
class TestAPIKeyScope:
    def test_full_scope_allows_all_methods(self, user):
        instance, _ = APIKey.generate(user, name="test", scope=APIKeyScope.FULL)
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            assert instance.allows_method(method) is True

    def test_read_scope_allows_only_get(self, user):
        instance, _ = APIKey.generate(user, name="test", scope=APIKeyScope.READ)
        assert instance.allows_method("GET") is True
        assert instance.allows_method("POST") is False
        assert instance.allows_method("DELETE") is False

    def test_write_scope_blocks_delete(self, user):
        instance, _ = APIKey.generate(user, name="test", scope=APIKeyScope.WRITE)
        assert instance.allows_method("GET") is True
        assert instance.allows_method("POST") is True
        assert instance.allows_method("DELETE") is False

    def test_custom_scope_model_check(self, user):
        instance, _ = APIKey.generate(
            user, name="test",
            scope=APIKeyScope.CUSTOM,
            allowed_models=["sales.SalesOrder"],
        )
        assert instance.allows_model("sales.SalesOrder") is True
        assert instance.allows_model("gyrokernel.Partner") is False

    def test_non_custom_scope_allows_any_model(self, user):
        instance, _ = APIKey.generate(user, name="test", scope=APIKeyScope.FULL)
        assert instance.allows_model("anything.Model") is True


@pytest.mark.django_db
class TestAPIKeyDeactivate:
    def test_deactivate_sets_inactive(self, user):
        instance, _ = APIKey.generate(user, name="test")
        instance.deactivate(reason="compromised")
        instance.refresh_from_db()
        assert instance.is_active is False
        assert instance.deactivated_reason == "compromised"
        assert instance.deactivated_at is not None

    def test_is_expired_false_for_no_expiry(self, user):
        instance, _ = APIKey.generate(user, name="test")
        assert instance.is_expired is False

    def test_is_expired_true_after_expiry(self, user):
        past = timezone.now() - timedelta(seconds=1)
        instance, _ = APIKey.generate(user, name="test", expires_at=past)
        assert instance.is_expired is True
