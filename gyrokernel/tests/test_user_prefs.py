"""Tests for UserPreferences and LoginLog."""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from gyrokernel.models import LoginLog, UserPreferences
from gyrokernel.models.user_ext import LoginEvent, Theme

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="prefuser", password="pass")


@pytest.mark.django_db
class TestUserPreferences:
    def test_create_defaults(self, user):
        prefs = UserPreferences.objects.create(user=user)
        assert prefs.timezone == "UTC"
        assert prefs.theme == Theme.SYSTEM
        assert prefs.records_per_page == 25
        assert prefs.notify_email is True
        assert prefs.two_factor_enabled is False

    def test_module_pref_roundtrip(self, user):
        prefs = UserPreferences.objects.create(user=user)
        prefs.set_module_pref("sales", "default_warehouse", "main")
        assert prefs.get_module_pref("sales", "default_warehouse") == "main"

    def test_module_pref_default(self, user):
        prefs = UserPreferences.objects.create(user=user)
        assert prefs.get_module_pref("sales", "missing_key", default=42) == 42

    def test_out_of_office_fields(self, user):
        from datetime import date

        prefs = UserPreferences.objects.create(
            user=user,
            out_of_office=True,
            out_of_office_message="Back next Monday",
            out_of_office_until=date(2026, 12, 31),
        )
        refreshed = UserPreferences.objects.get(pk=prefs.pk)
        assert refreshed.out_of_office is True
        assert refreshed.out_of_office_until.year == 2026

    def test_str_representation(self, user):
        prefs = UserPreferences(user=user)
        assert "prefuser" in str(prefs)

    def test_onetoone_uniqueness(self, user):
        UserPreferences.objects.create(user=user)
        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            UserPreferences.objects.create(user=user)


@pytest.mark.django_db
class TestLoginLog:
    def test_record_success(self, user):
        log = LoginLog.record(
            event=LoginEvent.SUCCESS,
            user=user,
            ip_address="127.0.0.1",
        )
        assert log.pk is not None
        assert log.event == LoginEvent.SUCCESS
        assert log.user == user

    def test_record_failed_with_username(self):
        log = LoginLog.record(
            event=LoginEvent.FAILED,
            username_attempted="hacker@evil.com",
            ip_address="10.0.0.1",
        )
        assert log.user is None
        assert log.username_attempted == "hacker@evil.com"

    def test_recent_failed_count(self, user):
        for _ in range(3):
            LoginLog.record(event=LoginEvent.FAILED, user=user)
        assert LoginLog.recent_failed_count(user, window_minutes=5) == 3

    def test_recent_failed_count_ignores_old(self, user):
        from datetime import timedelta

        log = LoginLog.objects.create(user=user, event=LoginEvent.FAILED)
        # Backdate via update() since auto_now_add ignores constructor values
        LoginLog.objects.filter(pk=log.pk).update(
            timestamp=timezone.now() - timedelta(hours=1)
        )
        assert LoginLog.recent_failed_count(user, window_minutes=5) == 0

    def test_str_representation(self, user):
        log = LoginLog(user=user, event=LoginEvent.SUCCESS, timestamp=timezone.now())
        assert "success" in str(log)
