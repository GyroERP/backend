"""GyroKernel Django app configuration and GyroAppConfig base class."""

from django.apps import AppConfig


class GyroAppConfig(AppConfig):
    """
    Base AppConfig for all GyroERP business apps.

    Each business app's apps.py should inherit this and declare the class
    attributes below. The kernel's AppRegistry reads these at startup to
    understand the full app dependency graph.

    Usage:

        class AccountingConfig(GyroAppConfig):
            name = "accounting"
            gyro_name = "Accounting"
            gyro_version = "1.0.0"
            gyro_depends = []
            gyro_category = "Finance"
            gyro_description = "Double-entry bookkeeping and financial reporting."
    """

    default_auto_field = "django.db.models.BigAutoField"

    gyro_name: str = ""
    gyro_version: str = "1.0.0"
    gyro_depends: list[str] = []
    gyro_category: str = "Generic"
    gyro_description: str = ""

    def is_gyro_app(self) -> bool:
        return bool(self.gyro_name)


class GyroKernelConfig(AppConfig):
    """App configuration for the GyroERP kernel itself."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "gyrokernel"
    verbose_name = "GyroERP Kernel"

    def ready(self) -> None:
        import gyrokernel.signals  # noqa: F401
