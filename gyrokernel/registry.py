"""AppRegistry — discovers and manages the state of all GyroERP apps."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.apps import apps

if TYPE_CHECKING:
    from gyrokernel.apps import GyroAppConfig
    from gyrokernel.models import InstalledApp

logger = logging.getLogger(__name__)


class AppRegistry:
    """
    Singleton service that understands the full GyroERP app graph.

    Two concerns are deliberately kept separate:
    - Django INSTALLED_APPS: which app code is loaded (static, set at startup)
    - InstalledApp DB records: which apps are logically active (dynamic, DB-managed)
    """

    def get_all_gyro_apps(self) -> list[GyroAppConfig]:
        """Return every AppConfig that subclasses GyroAppConfig and has gyro_name set."""
        from gyrokernel.apps import GyroAppConfig

        return [
            config
            for config in apps.get_app_configs()
            if isinstance(config, GyroAppConfig) and config.is_gyro_app()
        ]

    def get_installed_app_labels(self) -> set[str]:
        """Return app_labels currently marked as INSTALLED in the database."""
        from gyrokernel.models import AppState, InstalledApp

        return set(
            InstalledApp.objects.filter(state=AppState.INSTALLED).values_list(
                "app_label", flat=True
            )
        )

    def is_installed(self, app_label: str) -> bool:
        from gyrokernel.models import AppState, InstalledApp

        return InstalledApp.objects.filter(
            app_label=app_label, state=AppState.INSTALLED
        ).exists()

    def resolve_dependencies(self, app_label: str, _seen: set[str] | None = None) -> list[str]:
        """
        Return a topologically sorted list of app_labels that must be installed
        before app_label. The result does NOT include app_label itself.
        Raises ValueError for unknown apps or dependency cycles.
        """
        from gyrokernel.apps import GyroAppConfig

        if _seen is None:
            _seen = set()
        if app_label in _seen:
            return []
        _seen.add(app_label)

        try:
            config = apps.get_app_config(app_label)
        except LookupError:
            raise ValueError(
                f"Unknown app: '{app_label}'. Is it listed in INSTALLED_APPS?"
            )

        if not isinstance(config, GyroAppConfig):
            return []

        ordered: list[str] = []
        for dep in config.gyro_depends:
            sub_deps = self.resolve_dependencies(dep, _seen)
            for sd in sub_deps:
                if sd not in ordered:
                    ordered.append(sd)
            if dep not in ordered:
                ordered.append(dep)
        return ordered

    def get_dependents(self, app_label: str) -> list[str]:
        """Return app_labels of currently installed apps that depend on app_label.

        Checks both the DB-stored depends field (written at install time) and live
        GyroAppConfig metadata, so dependency blocking works even when AppConfig
        metadata and DB records are not perfectly in sync.
        """
        from gyrokernel.apps import GyroAppConfig
        from gyrokernel.models import AppState, InstalledApp

        # DB-first: fetch installed apps and check depends list in Python.
        # JSON array containment (`depends__contains`) is not portable across
        # all database backends (e.g. SQLite doesn't support it), so we do a
        # full scan of installed apps which is negligible at ERP app count.
        db_dependents = [
            app.app_label
            for app in InstalledApp.objects.filter(state=AppState.INSTALLED)
            if app_label in (app.depends or [])
        ]

        # Supplement with live AppConfig metadata (catches fresh installs not yet saved)
        installed = self.get_installed_app_labels()
        config_dependents = [
            config.app_label
            for config in apps.get_app_configs()
            if (
                isinstance(config, GyroAppConfig)
                and config.app_label in installed
                and app_label in config.gyro_depends
            )
        ]

        return list(dict.fromkeys(db_dependents + config_dependents))


registry = AppRegistry()
