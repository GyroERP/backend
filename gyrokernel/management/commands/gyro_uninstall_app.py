"""Management command: gyro_uninstall_app — deactivate a GyroERP app."""

from django.core.management.base import BaseCommand, CommandError

from gyrokernel.registry import registry
from gyrokernel.signals import app_uninstalled


class Command(BaseCommand):
    help = "Uninstall (deactivate) a GyroERP app by removing its InstalledApp record."

    def add_arguments(self, parser):
        parser.add_argument("app_label", help="Django app_label to uninstall, e.g. 'accounting'")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip dependent-app check and uninstall anyway.",
        )

    def handle(self, *args, **options):
        from gyrokernel.models import AppState, InstalledApp

        app_label = options["app_label"]

        try:
            installed_app = InstalledApp.objects.get(app_label=app_label)
        except InstalledApp.DoesNotExist:
            raise CommandError(f"App '{app_label}' is not currently installed.")

        if not options["force"]:
            dependents = registry.get_dependents(app_label)
            if dependents:
                raise CommandError(
                    f"Cannot uninstall '{app_label}': the following installed apps depend on it: "
                    + ", ".join(dependents)
                    + ". Uninstall them first, or re-run with --force."
                )

        installed_app.state = AppState.UNINSTALLING
        installed_app.save(update_fields=["state"])

        app_uninstalled.send(sender=self.__class__, app_label=app_label)

        installed_app.delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully uninstalled '{app_label}'."))
