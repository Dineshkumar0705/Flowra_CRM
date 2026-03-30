"""
Notification and ActivityLog models.

Notification — in-app alerts for users (deal won, new lead, etc.)
ActivityLog — immutable audit trail of every significant action.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class NotificationType(str, enum.Enum):
    DEAL_WON = "deal_won"
    NEW_LEAD = "new_lead"
    OVERDUE_TASK = "overdue_task"
    PAYMENT_FAILED = "payment_failed"
    TEAM_MENTION = "team_mention"
    WHATSAPP_RECEIVED = "whatsapp_received"
    EMAIL_RECEIVED = "email_received"
    AUTOPILOT_COMPLETED = "autopilot_completed"
    SYSTEM = "system"


class Notification(TimestampMixin, Base):
    """
    An in-app notification for a specific user within a workspace.

    read_at is set when the user reads (or dismisses) the notification.
    action_url lets the frontend deep-link to the relevant entity.
    """

    __tablename__ = "notifications"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_notification_user", "workspace_id", "user_id"),
        Index("idx_notification_unread", "user_id", "read_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.notification_type} user={self.user_id}>"

    @property
    def is_read(self) -> bool:
        return self.read_at is not None


# ---------------------------------------------------------------------------
# ActivityLog (Audit Trail)
# ---------------------------------------------------------------------------

class ActivityLog(TimestampMixin, Base):
    """
    Immutable audit log.

    Every significant action in the CRM is recorded here.
    Records are NEVER soft-deleted — this is the permanent trail.
    old_value / new_value store JSON snapshots for diff views.
    """

    __tablename__ = "activity_logs"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    old_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_value: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # supports IPv6
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_activity_workspace_entity", "workspace_id", "entity_type", "entity_id"),
        Index("idx_activity_user", "workspace_id", "user_id"),
        Index("idx_activity_created", "workspace_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ActivityLog {self.entity_type}.{self.action} entity={self.entity_id}>"
