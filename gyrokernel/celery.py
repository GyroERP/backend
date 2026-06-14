"""Celery application instance for GyroERP."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gyroerp.settings.development")

app = Celery("gyrokernel")

# Read Celery config from Django settings (all keys with CELERY_ prefix)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in every app listed in INSTALLED_APPS
app.autodiscover_tasks()
