"""
Deal model.

A deal represents a sales opportunity.  Deals are workspace-scoped and
optionally linked to a Contact.  Stage transitions trigger the automation
engine (handled in DealService).
"""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DealStage(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class DealPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Deal
# ---------------------------------------------------------------------------

class Deal(TimestampMixin, SoftDeleteMixin, Base):
    """
    A sales opportunity in the CRM pipeline.

    Financial fields use Float (sufficient for INR amounts up to ~10 crore).
    For accounting-grade precision, switch to Numeric(14, 2).
    """

    __tablename__ = "deals"

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
    # Basic info
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Financial
    # ------------------------------------------------------------------
    value: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------
    stage: Mapped[DealStage] = mapped_column(
        Enum(DealStage), default=DealStage.NEW, nullable=False, index=True
    )
    priority: Mapped[DealPriority] = mapped_column(
        Enum(DealPriority), default=DealPriority.MEDIUM, nullable=False
    )
    probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expected_close_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Ownership & linking
    # ------------------------------------------------------------------
    owner_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pipeline_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ------------------------------------------------------------------
    # Source & AI
    # ------------------------------------------------------------------
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Lifecycle timestamps
    # ------------------------------------------------------------------
    won_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    lost_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="deals")  # type: ignore[name-defined]
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="deals")  # type: ignore[name-defined]
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])  # type: ignore[name-defined]
    pipeline: Mapped[Optional["Pipeline"]] = relationship("Pipeline", back_populates="deals")  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # DB constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_deal_value_positive"),
        CheckConstraint("probability >= 0 AND probability <= 100", name="ck_deal_probability_range"),
        Index("idx_deal_workspace_stage", "workspace_id", "stage"),
        Index("idx_deal_owner", "workspace_id", "owner_id"),
        Index("idx_deal_contact", "contact_id"),
        Index("idx_deal_pipeline", "pipeline_id"),
    )

    def __repr__(self) -> str:
        return f"<Deal id={self.id} title='{self.title}' stage={self.stage}>"

    # ------------------------------------------------------------------
    # Business methods
    # ------------------------------------------------------------------
    def mark_won(self) -> None:
        self.stage = DealStage.WON
        self.probability = 100.0
        self.won_at = datetime.now(timezone.utc)

    def mark_lost(self) -> None:
        self.stage = DealStage.LOST
        self.probability = 0.0
        self.lost_at = datetime.now(timezone.utc)

    def expected_value(self) -> float:
        """Weighted deal value used in pipeline forecasting."""
        return (self.value or 0.0) * (self.probability or 0.0) / 100.0

    @property
    def is_open(self) -> bool:
        return self.stage not in (DealStage.WON, DealStage.LOST)
