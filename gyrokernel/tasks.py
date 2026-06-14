"""Celery tasks for the GyroERP kernel."""

import importlib
import logging

from gyrokernel.celery import app

logger = logging.getLogger(__name__)


@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="gyrokernel.run_scheduled_action",
)
def run_scheduled_action(self, task_path: str, *args, **kwargs) -> dict:
    """
    Universal runner for GyroERP scheduled actions.

    Dynamically imports and calls any callable by its dotted Python path.
    Register django-celery-beat PeriodicTask entries pointing to this task
    with `task_path` as the first positional argument.

    Example:
        task_path = "accounting.tasks.close_monthly_period"
    """
    try:
        module_path, func_name = task_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        result = func(*args, **kwargs)
        logger.info("Scheduled action completed: %s", task_path)
        return {"status": "ok", "task_path": task_path, "result": str(result)}
    except Exception as exc:
        logger.exception("Scheduled action failed: %s", task_path)
        raise self.retry(exc=exc) from exc
