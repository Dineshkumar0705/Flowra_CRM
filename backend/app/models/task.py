"""
Task model — to-do items tied to contacts or deals.

Tasks are workspace-scoped and optionally linked to a Contact and/or Deal.
They support priorities, due dates, recurrence hints, and soft-deletes.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class TaskStatus(str, enum.Enum):
    TODO       = "todo"
    IN_PROGRESS = "in_progress"
    DONE       = "done"
    CANCELLED  = "cancelled"


class TaskPriority(str, enum.Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"


class Task(TimestampMixin, SoftDeleteMixin, Base):
    """
    A task that belongs to a workspace, optionally linked to a contact and/or deal.

    Design decisions:
    - workspace_id on every row for multi-tenancy (enforced at service layer)
    - contact_id / deal_id are optional — a task can be standalone
    - due_at stores the deadline in UTC
    - completed_at is set when status transitions to DONE
    """

    __tablename__ = "tasks"

    # ------------------------------------------------------------------
    # Multi-tenancy
    # ------------------------------------------------------------------
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    title: Mapped[str]       = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Status & priority
    # ------------------------------------------------------------------
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.TODO, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False, index=True
    )

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------
    due_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Relations (all optional)
    # ------------------------------------------------------------------
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deal_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # ORM relationships
    # ------------------------------------------------------------------
    workspace:   Mapped["Workspace"]       = relationship("Workspace")                        # type: ignore[name-defined]
    contact:     Mapped[Optional["Contact"]] = relationship("Contact")                        # type: ignore[name-defined]
    deal:        Mapped[Optional["Deal"]]    = relationship("Deal")                           # type: ignore[name-defined]
    assignee:    Mapped[Optional["User"]]    = relationship("User", foreign_keys=[assigned_to])  # type: ignore[name-defined]
    creator:     Mapped[Optional["User"]]    = relationship("User", foreign_keys=[created_by])   # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_task_workspace_status",   "workspace_id", "status"),
        Index("idx_task_workspace_due",      "workspace_id", "due_at"),
        Index("idx_task_workspace_assignee", "workspace_id", "assigned_to"),
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"

    @property
    def is_overdue(self) -> bool:
        from datetime import timezone
        if self.due_at and self.status not in (TaskStatus.DONE, TaskStatus.CANCELLED):
            return datetime.now(timezone.utc) > self.due_at
        return False
