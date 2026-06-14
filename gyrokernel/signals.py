"""Signal definitions for the GyroERP kernel."""

from django.dispatch import Signal

# Fired after an app is activated via gyro_install_app
# kwargs: app_label (str), installed_app (InstalledApp)
app_installed = Signal()

# Fired before an app record is removed via gyro_uninstall_app
# kwargs: app_label (str)
app_uninstalled = Signal()
