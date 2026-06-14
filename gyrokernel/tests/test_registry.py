"""Tests for AppRegistry and the install/uninstall management commands."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from gyrokernel.models import AppState, InstalledApp
from gyrokernel.registry import registry


@pytest.mark.django_db
class TestAppRegistry:
    def test_get_all_gyro_apps_returns_gyro_app_configs_only(self):
        from gyrokernel.apps import GyroAppConfig

        for config in registry.get_all_gyro_apps():
            assert isinstance(config, GyroAppConfig)
            assert config.gyro_name

    def test_gyrokernel_itself_excluded_from_gyro_apps(self):
        labels = [a.app_label for a in registry.get_all_gyro_apps()]
        assert "gyrokernel" not in labels

    def test_is_installed_false_when_no_db_record(self):
        assert registry.is_installed("accounting") is False

    def test_is_installed_true_with_db_record(self):
        InstalledApp.objects.create(
            app_label="accounting",
            gyro_name="Accounting",
            version="1.0.0",
            state=AppState.INSTALLED,
        )
        assert registry.is_installed("accounting") is True

    def test_is_installed_false_for_non_installed_state(self):
        InstalledApp.objects.create(
            app_label="crm",
            gyro_name="CRM",
            version="1.0.0",
            state=AppState.UNINSTALLING,
        )
        assert registry.is_installed("crm") is False

    def test_resolve_dependencies_unknown_app_raises(self):
        with pytest.raises(ValueError, match="Unknown app"):
            registry.resolve_dependencies("this_app_does_not_exist_xyz")

    def test_get_dependents_returns_empty_when_none(self):
        assert registry.get_dependents("accounting") == []

    def test_get_installed_app_labels(self):
        InstalledApp.objects.create(
            app_label="hr", gyro_name="HR", version="1.0.0", state=AppState.INSTALLED
        )
        InstalledApp.objects.create(
            app_label="payroll", gyro_name="Payroll", version="1.0.0", state=AppState.UNINSTALLING
        )
        labels = registry.get_installed_app_labels()
        assert "hr" in labels
        assert "payroll" not in labels


@pytest.mark.django_db
class TestInstallAppCommand:
    def test_install_standard_django_app_raises(self):
        with pytest.raises(CommandError):
            call_command("gyro_install_app", "auth")

    def test_install_unknown_app_raises(self):
        with pytest.raises(CommandError):
            call_command("gyro_install_app", "totally_nonexistent_app_xyz")


@pytest.mark.django_db
class TestUninstallAppCommand:
    def test_uninstall_not_installed_raises(self):
        with pytest.raises(CommandError):
            call_command("gyro_uninstall_app", "accounting")

    def test_uninstall_removes_installed_app_record(self):
        InstalledApp.objects.create(
            app_label="sales",
            gyro_name="Sales",
            version="1.0.0",
            state=AppState.INSTALLED,
        )
        call_command("gyro_uninstall_app", "sales")
        assert not InstalledApp.objects.filter(app_label="sales").exists()

    def test_uninstall_blocked_by_dependents(self):
        # accounting is a dependency; invoicing declares it in the DB depends field
        InstalledApp.objects.create(
            app_label="accounting",
            gyro_name="Accounting",
            version="1.0.0",
            state=AppState.INSTALLED,
            depends=[],
        )
        InstalledApp.objects.create(
            app_label="invoicing",
            gyro_name="Invoicing",
            version="1.0.0",
            state=AppState.INSTALLED,
            depends=["accounting"],
        )
        with pytest.raises(CommandError, match="depend"):
            call_command("gyro_uninstall_app", "accounting")
