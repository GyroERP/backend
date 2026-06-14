"""Management command: gyro_install_app — activate a GyroERP app."""

from django.core.management.base import BaseCommand, CommandError

from gyrokernel.registry import registry
from gyrokernel.signals import app_installed


class Command(BaseCommand):
    help = "Install (activate) a GyroERP app by creating its InstalledApp record."

    def add_arguments(self, parser):
        parser.add_argument("app_label", help="Django app_label to install, e.g. 'accounting'")
        parser.add_argument(
            "--user",
            metavar="USERNAME",
            help="Username to record as the installer (optional)",
        )

    def handle(self, *args, **options):
        from django.apps import apps as django_apps

        from gyrokernel.apps import GyroAppConfig

        app_label = options["app_label"]

        try:
            config = django_apps.get_app_config(app_label)
        except LookupError:
            raise CommandError(
                f"App '{app_label}' is not in INSTALLED_APPS. "
                "Add it to INSTALLED_APPS before activating."
            )

        if not isinstance(config, GyroAppConfig):
            raise CommandError(
                f"App '{app_label}' does not extend GyroAppConfig. "
                "Only GyroERP apps can be installed via this command."
            )

        if not config.gyro_name:
            raise CommandError(
                f"App '{app_label}' has no gyro_name declared in its GyroAppConfig."
            )

        # Install declared dependencies first
        deps = registry.resolve_dependencies(app_label)
        for dep in deps:
            if not registry.is_installed(dep):
                self.stdout.write(f"  Auto-installing dependency: {dep}")
                self._activate(dep, options.get("user"))

        self._activate(app_label, options.get("user"))
        self.stdout.write(self.style.SUCCESS(f"Successfully installed '{app_label}'."))

    def _activate(self, app_label: str, username: str | None) -> None:
        from django.apps import apps as django_apps
        from django.contrib.auth import get_user_model

        from gyrokernel.apps import GyroAppConfig
        from gyrokernel.models import AppState, InstalledApp

        config = django_apps.get_app_config(app_label)
        if not isinstance(config, GyroAppConfig):
            return

        user = None
        if username:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stderr.write(
                    f"Warning: user '{username}' not found; recording no installer."
                )

        installed_app, created = InstalledApp.objects.update_or_create(
            app_label=app_label,
            defaults={
                "gyro_name": config.gyro_name,
                "version": config.gyro_version,
                "state": AppState.INSTALLED,
                "depends": config.gyro_depends,
                "category": config.gyro_category,
                "description": config.gyro_description,
                "installed_by": user,
            },
        )

        app_installed.send(
            sender=self.__class__,
            app_label=app_label,
            installed_app=installed_app,
        )

        verb = "Registered" if created else "Updated"
        self.stdout.write(f"  {verb}: {config.gyro_name} v{config.gyro_version}")
