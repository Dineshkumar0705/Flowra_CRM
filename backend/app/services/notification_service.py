"""
Notification and ActivityLog service.

Creates in-app notifications and writes to the immutable audit trail.
Both are workspace-scoped.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.notification import ActivityLog, Notification, NotificationType

log = logging.getLogger("flowra.service.notification")


class NotificationService:
    """Manages in-app notifications and the audit activity log."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def create(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        body: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Create and persist a new notification for a user."""
        notif = Notification(
            workspace_id=self.workspace_id,
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            metadata_=metadata,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        log.info("notification.created", user_id=user_id, type=notification_type)
        return notif

    def list_for_user(
        self,
        user_id: str,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 30,
    ) -> Tuple[List[Notification], int]:
        q = self.db.query(Notification).filter(
            Notification.workspace_id == self.workspace_id,
            Notification.user_id == user_id,
        )
        if unread_only:
            q = q.filter(Notification.read_at.is_(None))

        total = q.count()
        items = q.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def mark_read(self, user_id: str, notification_ids: List[str]) -> int:
        """Mark specific notifications as read. Returns count updated."""
        now = datetime.now(timezone.utc)
        updated = (
            self.db.query(Notification)
            .filter(
                Notification.workspace_id == self.workspace_id,
                Notification.user_id == user_id,
                Notification.id.in_(notification_ids),
                Notification.read_at.is_(None),
            )
            .update({"read_at": now}, synchronize_session=False)
        )
        self.db.commit()
        return updated

    def mark_all_read(self, user_id: str) -> int:
        """Mark all unread notifications as read for a user."""
        now = datetime.now(timezone.utc)
        updated = (
            self.db.query(Notification)
            .filter(
                Notification.workspace_id == self.workspace_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .update({"read_at": now}, synchronize_session=False)
        )
        self.db.commit()
        return updated

    def unread_count(self, user_id: str) -> int:
        return (
            self.db.query(Notification)
            .filter(
                Notification.workspace_id == self.workspace_id,
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Activity log (audit trail — immutable)
    # ------------------------------------------------------------------

    def log_activity(
        self,
        entity_type: str,
        action: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> ActivityLog:
        """
        Write an immutable audit log entry.

        This method never raises — if it fails, it logs the error and
        returns gracefully so the main operation is not disrupted.
        """
        try:
            entry = ActivityLog(
                workspace_id=self.workspace_id,
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                old_value=old_value,
                new_value=new_value,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception as exc:
            log.error("activity_log.write_failed", error=str(exc))
            self.db.rollback()
            # Return a dummy non-persisted entry so callers don't crash
            return ActivityLog(
                workspace_id=self.workspace_id,
                entity_type=entity_type,
                action=action,
            )

    def get_activity_log(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ActivityLog], int]:
        q = self.db.query(ActivityLog).filter(
            ActivityLog.workspace_id == self.workspace_id
        )
        if entity_type:
            q = q.filter(ActivityLog.entity_type == entity_type)
        if entity_id:
            q = q.filter(ActivityLog.entity_id == entity_id)
        if user_id:
            q = q.filter(ActivityLog.user_id == user_id)

        total = q.count()
        items = q.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
