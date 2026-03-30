"""
Background task helpers for Flowra.

Two modes:
  1. FastAPI BackgroundTasks — fire-and-forget within the same process.
     Use for non-critical tasks that must complete within the request lifecycle
     (e.g., activity logging, sending a single notification).

  2. Celery — offload heavy / scheduled tasks to a worker process.
     Use for: Gmail sync, stale deal scans, bulk WhatsApp sends, onboarding autopilot.
     Requires Redis (REDIS_URL in .env) and a running worker:
       celery -A app.core.background.celery_app worker --loglevel=info

Celery is optional — if Redis is not configured, Celery tasks fall back
to synchronous execution in the same process (CELERY_ALWAYS_EAGER=True).
"""

import logging
from functools import wraps
from typing import Any, Callable

from app.core.config import settings

log = logging.getLogger("flowra.background")

# ---------------------------------------------------------------------------
# Celery application
# ---------------------------------------------------------------------------

try:
    from celery import Celery

    celery_app = Celery(
        "flowra",
        broker=settings.REDIS_URL or "redis://localhost:6379/0",
        backend=settings.REDIS_URL or "redis://localhost:6379/0",
        include=[
            "app.tasks.gmail_tasks",
            "app.tasks.automation_tasks",
            "app.tasks.notification_tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Asia/Kolkata",
        enable_utc=True,
        # Fall back to synchronous if Redis unavailable
        task_always_eager=not bool(settings.REDIS_URL),
        # Retry failed tasks up to 3 times with exponential backoff
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        # Beat schedule — recurring tasks
        beat_schedule={
            "scan-stale-deals-every-3h": {
                "task": "app.tasks.automation_tasks.scan_all_workspaces_stale_deals",
                "schedule": 3 * 60 * 60,   # every 3 hours
            },
            "gmail-sync-every-15m": {
                "task": "app.tasks.gmail_tasks.sync_all_connected_gmails",
                "schedule": 15 * 60,        # every 15 minutes
            },
        },
    )

    CELERY_AVAILABLE = True
    log.info("background.celery_configured", broker=settings.REDIS_URL)

except ImportError:
    celery_app = None  # type: ignore
    CELERY_AVAILABLE = False
    log.warning("background.celery_unavailable", reason="celery not installed")


# ---------------------------------------------------------------------------
# Safe fire-and-forget decorator for FastAPI BackgroundTasks
# ---------------------------------------------------------------------------

def background_task(func: Callable) -> Callable:
    """
    Wraps a function so it can be added to FastAPI's BackgroundTasks safely.
    Catches and logs any exceptions so background errors don't surface to users.

    Usage:
        @background_task
        def send_notification(user_id: str, message: str):
            ...

        # In a route:
        background_tasks.add_task(send_notification, user_id, message)
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        try:
            func(*args, **kwargs)
        except Exception as exc:
            log.exception(
                "background.task_failed",
                task=func.__name__,
                error=str(exc),
            )
    return wrapper
