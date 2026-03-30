"""
Workspace and WorkspaceMember models.

A Workspace is the top-level multi-tenancy unit in Flowra.  Every other
entity (contacts, deals, pipelines, …) is scoped to a workspace_id.

WorkspaceMember links users to workspaces with a role (owner / admin / member).
"""

import enum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WorkspacePlan(str, enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    AGENCY = "agency"


class MemberRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

class Workspace(TimestampMixin, SoftDeleteMixin, Base):
    """
    SaaS tenant unit.

    One agency / company = one workspace.
    All data queries MUST be scoped with workspace_id.
    """

    __tablename__ = "workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    plan: Mapped[WorkspacePlan] = mapped_column(
        Enum(WorkspacePlan), default=WorkspacePlan.STARTER, nullable=False, index=True
    )
    plan_expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id], back_populates="owned_workspaces")  # type: ignore[name-defined]
    members: Mapped[list["WorkspaceMember"]] = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    contacts: Mapped[list["Contact"]] = relationship("Contact", back_populates="workspace", cascade="all, delete-orphan")  # type: ignore[name-defined]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="workspace", cascade="all, delete-orphan")  # type: ignore[name-defined]
    pipelines: Mapped[list["Pipeline"]] = relationship("Pipeline", back_populates="workspace", cascade="all, delete-orphan")  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("idx_workspace_owner", "owner_id"),
        Index("idx_workspace_plan", "plan"),
    )

    def __repr__(self) -> str:
        return f"<Workspace id={self.id} slug={self.slug} plan={self.plan}>"


# ---------------------------------------------------------------------------
# WorkspaceMember
# ---------------------------------------------------------------------------

class WorkspaceMember(TimestampMixin, Base):
    """
    Junction table linking users to workspaces with a role.

    A user can belong to multiple workspaces (agency model).
    """

    __tablename__ = "workspace_members"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[MemberRole] = mapped_column(
        Enum(MemberRole), default=MemberRole.MEMBER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="workspace_memberships")  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),
        Index("idx_member_workspace", "workspace_id"),
        Index("idx_member_user", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMember workspace={self.workspace_id} user={self.user_id} role={self.role}>"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def is_owner(self) -> bool:
        return self.role == MemberRole.OWNER

    def is_admin_or_above(self) -> bool:
        return self.role in (MemberRole.OWNER, MemberRole.ADMIN)
