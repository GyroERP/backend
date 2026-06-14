"""Tests for the run_scheduled_action Celery task."""

import pytest


def _sample_action(message: str = "hello") -> str:
    return f"done: {message}"


@pytest.fixture(autouse=True)
def _force_eager(settings):
    """Run Celery tasks synchronously so tests don't need a broker."""
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


class TestRunScheduledAction:
    def test_successful_call_returns_ok_status(self):
        from gyrokernel.tasks import run_scheduled_action

        # Use the real _sample_action function defined in this module
        task_path = "gyrokernel.tests.test_scheduled_actions._sample_action"
        result = run_scheduled_action.apply(
            args=[task_path], kwargs={"message": "world"}
        ).get()

        assert result["status"] == "ok"
        assert result["task_path"] == task_path
        assert "done: world" in result["result"]

    def test_invalid_module_path_raises(self):
        from gyrokernel.tasks import run_scheduled_action

        with pytest.raises(Exception):
            run_scheduled_action.apply(
                args=["gyrokernel.tests.test_scheduled_actions.nonexistent"]
            ).get()

    def test_task_is_registered_by_name(self):
        from gyrokernel.celery import app

        assert "gyrokernel.run_scheduled_action" in app.tasks
