"""
Pipeline, PipelineStage, and DealPipelineMap models.

A Pipeline is a ordered sequence of Stages through which Deals progress.
DealPipelineMap is the Kanban engine — it tracks which stage a deal is in
and records how long it spent there (for analytics).
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Pipeline(TimestampMixin, Base):
    """
    A named pipeline (e.g., "Sales Pipeline", "Onboarding Pipeline").

    Each workspace can have multiple pipelines.
    One pipeline can be flagged as the default.
    """

    __tablename__ = "pipelines"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="pipelines")  # type: ignore[name-defined]
    stages: Mapped[list["PipelineStage"]] = relationship(
        "PipelineStage",
        back_populates="pipeline",
        cascade="all, delete-orphan",
        order_by="PipelineStage.order",
    )
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="pipeline")  # type: ignore[name-defined]

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_pipeline_name_per_workspace"),
        Index("idx_pipeline_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<Pipeline id={self.id} name='{self.name}'>"


# ---------------------------------------------------------------------------
# PipelineStage
# ---------------------------------------------------------------------------

class PipelineStage(TimestampMixin, Base):
    """
    A single stage within a pipeline (e.g., "Lead", "Proposal", "Won").

    Stages are ordered.  Win/loss flags drive automation and analytics.
    """

    __tablename__ = "pipeline_stages"

    pipeline_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    probability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#3B82F6", nullable=False)
    is_won_stage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost_stage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    automation_rules: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="stages")
    deal_mappings: Mapped[list["DealPipelineMap"]] = relationship(
        "DealPipelineMap", back_populates="stage", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("pipeline_id", "order", name="uq_stage_order"),
        UniqueConstraint("pipeline_id", "name", name="uq_stage_name"),
        CheckConstraint("probability >= 0 AND probability <= 100", name="ck_stage_probability"),
        Index("idx_stage_pipeline", "pipeline_id"),
    )

    def __repr__(self) -> str:
        return f"<PipelineStage id={self.id} name='{self.name}' order={self.order}>"

    @property
    def is_terminal(self) -> bool:
        return self.is_won_stage or self.is_lost_stage


# ---------------------------------------------------------------------------
# DealPipelineMap  (Kanban engine)
# ---------------------------------------------------------------------------

class DealPipelineMap(TimestampMixin, Base):
    """
    Maps a deal to a specific stage within a pipeline.

    Key feature: records entered_at / exited_at so we can compute
    "time in stage" for velocity analytics.
    """

    __tablename__ = "deal_pipeline_map"

    deal_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pipeline_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("pipeline_stages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Stage timing analytics
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    exited_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    stage: Mapped[Optional[PipelineStage]] = relationship("PipelineStage", back_populates="deal_mappings")

    __table_args__ = (
        UniqueConstraint("deal_id", "pipeline_id", name="uq_deal_pipeline"),
        Index("idx_deal_map_stage", "stage_id", "position"),
    )

    def __repr__(self) -> str:
        return f"<DealPipelineMap deal={self.deal_id} stage={self.stage_id}>"

    def move_to_stage(self, new_stage_id: str) -> None:
        """Record stage transition, preserving time-in-stage for analytics."""
        now = datetime.now(timezone.utc)
        if self.entered_at:
            self.exited_at = now
            self.duration_seconds = (now - self.entered_at).total_seconds()

        self.stage_id = new_stage_id
        self.entered_at = now
        self.exited_at = None

    def time_in_stage_seconds(self) -> Optional[float]:
        """Return seconds the deal has been in its current stage."""
        if not self.entered_at:
            return None
        return (datetime.now(timezone.utc) - self.entered_at).total_seconds()
