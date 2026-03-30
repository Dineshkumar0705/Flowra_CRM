"""
Flowra SQLAlchemy base mixin.

Every model in the codebase should inherit from TimestampMixin (and optionally
SoftDeleteMixin) so that UUID PKs, created_at, updated_at, and deleted_at are
consistent across all 14+ tables.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    """Return a new UUID4 as a hex string (stored as VARCHAR(36))."""
    return str(uuid.uuid4())


class TimestampMixin:
    """
    Mixin that adds UUID primary key + created_at / updated_at to any model.

    All times are stored in UTC (the DB connection is forced to UTC in
    database.py).
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=_new_uuid,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_now,
        onupdate=_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"


class SoftDeleteMixin:
    """
    Mixin that adds a nullable deleted_at column for soft-deletes.

    Every repository that uses this mixin MUST add a filter:
        .filter(Model.deleted_at.is_(None))
    to all list / get queries.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        """Convenience property — True if the record has been soft-deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as deleted without removing it from the database."""
        self.deleted_at = _now()
