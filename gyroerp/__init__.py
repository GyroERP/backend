"""GyroERP backend API."""

__version__ = "0.1.0"

from gyrokernel.celery import app as celery_app

__all__ = ("celery_app",)
