"""
Celery tasks — notification delivery.
"""

import logging
from typing import List, Optional

log = logging.getLogger("flowra.tasks.notifications")


def send_notification_to_user(
    workspace_id: str,
    user_id: str,
    notification_type: str,
    title: str,
    body: str,
    action_url: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """
    Create a persistent notification in the DB and push to WebSocket if connected.
    Safe to call from any service without worrying about DB session lifecycle.
    """
    from app.core.database import SessionLocal
    from app.services.notification_service import NotificationService

    db = SessionLocal()
    try:
        svc = NotificationService(db, workspace_id)
        notification = svc.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            metadata=metadata or {},
        )

        # Push to WebSocket connection manager (non-fatal if not connected)
        try:
            from app.api.routes.notifications import manager
            import asyncio
            asyncio.run(manager.send_to_user(user_id, {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "title": title,
                    "body": body,
                    "action_url": action_url,
                },
            }))
        except Exception:
            pass  # WebSocket push is best-effort

        log.info("notification.sent", user_id=user_id, type=notification_type)
        return notification.id
    finally:
        db.close()


# Register as Celery task if available
try:
    from app.core.background import celery_app
    if celery_app is not None:
        send_notification_to_user = celery_app.task(
            name="app.tasks.notification_tasks.send_notification_to_user",
            bind=True,
            max_retries=3,
            default_retry_delay=10,
        )(send_notification_to_user)
except ImportError:
    pass
