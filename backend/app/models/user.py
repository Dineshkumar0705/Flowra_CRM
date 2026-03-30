"""
User model.

Users are global (not scoped to a workspace) but gain access to data only
through WorkspaceMember rows.  This allows a single user to belong to
multiple workspaces (e.g., an agency employee working across client accounts).
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"   # platform-level admin (Flowra staff)
    ADMIN = "admin"               # workspace admin
    MANAGER = "manager"
    SALES = "sales"
    VIEWER = "viewer"


class User(TimestampMixin, SoftDeleteMixin, Base):
    """
    Platform user.

    Authentication is via JWT (email + bcrypt password).
    Google OAuth is planned but not yet implemented.
    """

    __tablename__ = "users"

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ------------------------------------------------------------------
    # Role & access
    # ------------------------------------------------------------------
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.SALES, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # ------------------------------------------------------------------
    # Security / login tracking
    # ------------------------------------------------------------------
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Preferences
    # ------------------------------------------------------------------
    preferences: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    owned_workspaces: Mapped[list["Workspace"]] = relationship(  # type: ignore[name-defined]
        "Workspace",
        foreign_keys="Workspace.owner_id",
        back_populates="owner",
    )
    workspace_memberships: Mapped[list["WorkspaceMember"]] = relationship(  # type: ignore[name-defined]
        "WorkspaceMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

    # ------------------------------------------------------------------
    # Business helpers
    # ------------------------------------------------------------------
    def is_account_locked(self) -> bool:
        """Return True if the account is currently locked."""
        if self.locked_until:
            return self.locked_until > datetime.now(timezone.utc)
        return False

    def record_login_success(self) -> None:
        """Update login tracking fields after a successful login."""
        self.last_login = datetime.now(timezone.utc)
        self.login_count += 1
        self.failed_attempts = 0
        self.locked_until = None

    def record_login_failure(self) -> None:
        """Increment failed attempt counter and lock account after 5 failures."""
        from datetime import timedelta

        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

    def is_admin_or_above(self) -> bool:
        return self.role in (UserRole.SUPER_ADMIN, UserRole.ADMIN)
