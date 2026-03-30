"""Deal repository — workspace-scoped, pagination-ready, analytics-optimised."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.deal import Deal, DealStage

log = logging.getLogger("flowra.repo.deal")


class DealRepository:
    """CRUD + analytics for the Deal table."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id

    def _base_q(self):
        return self.db.query(Deal).filter(
            Deal.workspace_id == self.workspace_id,
            Deal.deleted_at.is_(None),
        )

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, data: Dict[str, Any]) -> Deal:
        data["workspace_id"] = self.workspace_id
        deal = Deal(**data)
        self.db.add(deal)
        self.db.commit()
        self.db.refresh(deal)
        log.info("deal.created", workspace=self.workspace_id, deal_id=deal.id)
        return deal

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, deal_id: str) -> Optional[Deal]:
        return self._base_q().filter(Deal.id == deal_id).first()

    # ------------------------------------------------------------------
    # List + filters
    # ------------------------------------------------------------------

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        stage: Optional[DealStage] = None,
        priority=None,
        owner_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        search: Optional[str] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> Tuple[List[Deal], int]:
        q = self._base_q()

        if stage:
            q = q.filter(Deal.stage == stage)
        if priority:
            q = q.filter(Deal.priority == priority)
        if owner_id:
            q = q.filter(Deal.owner_id == owner_id)
        if contact_id:
            q = q.filter(Deal.contact_id == contact_id)
        if pipeline_id:
            q = q.filter(Deal.pipeline_id == pipeline_id)
        if min_value is not None:
            q = q.filter(Deal.value >= min_value)
        if max_value is not None:
            q = q.filter(Deal.value <= max_value)
        if search:
            term = f"%{search}%"
            q = q.filter(
                or_(Deal.title.ilike(term), Deal.description.ilike(term))
            )

        total = q.count()
        items = q.order_by(Deal.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, deal: Deal, data: Dict[str, Any]) -> Deal:
        for k, v in data.items():
            if hasattr(deal, k):
                setattr(deal, k, v)
        deal.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(deal)
        return deal

    # ------------------------------------------------------------------
    # Stage transition
    # ------------------------------------------------------------------

    def move_stage(self, deal: Deal, new_stage: DealStage) -> Deal:
        old_stage = deal.stage
        if new_stage == DealStage.WON:
            deal.mark_won()
        elif new_stage == DealStage.LOST:
            deal.mark_lost()
        else:
            deal.stage = new_stage
            deal.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(deal)
        log.info("deal.stage_changed", deal_id=deal.id, old_stage=old_stage, new_stage=new_stage)
        return deal

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------

    def soft_delete(self, deal: Deal) -> None:
        deal.soft_delete()
        self.db.commit()

    # ------------------------------------------------------------------
    # Analytics queries (DB-level aggregations — fast)
    # ------------------------------------------------------------------

    def total_value(self) -> float:
        result = self.db.query(func.sum(Deal.value)).filter(
            Deal.workspace_id == self.workspace_id, Deal.deleted_at.is_(None)
        ).scalar()
        return float(result or 0.0)

    def pipeline_value(self) -> float:
        """Weighted pipeline value = sum(value × probability / 100)."""
        result = self.db.query(
            func.sum(Deal.value * Deal.probability / 100.0)
        ).filter(
            Deal.workspace_id == self.workspace_id,
            Deal.deleted_at.is_(None),
            Deal.stage.notin_([DealStage.WON, DealStage.LOST]),
        ).scalar()
        return float(result or 0.0)

    def stage_distribution(self) -> Dict[str, int]:
        rows = (
            self.db.query(Deal.stage, func.count(Deal.id))
            .filter(Deal.workspace_id == self.workspace_id, Deal.deleted_at.is_(None))
            .group_by(Deal.stage)
            .all()
        )
        return {str(stage): int(count) for stage, count in rows}

    def win_rate(self) -> float:
        total = self._base_q().count()
        if total == 0:
            return 0.0
        won = self._base_q().filter(Deal.stage == DealStage.WON).count()
        return round((won / total) * 100, 2)

    def top_deals(self, limit: int = 5) -> List[Deal]:
        return (
            self._base_q()
            .filter(Deal.stage.notin_([DealStage.WON, DealStage.LOST]))
            .order_by(Deal.value.desc())
            .limit(limit)
            .all()
        )

    def revenue_by_date(self, since: datetime) -> List[Dict[str, Any]]:
        """Return daily revenue for closed-won deals since a given date."""
        rows = (
            self.db.query(
                func.date(Deal.won_at).label("date"),
                func.sum(Deal.value).label("revenue"),
                func.count(Deal.id).label("count"),
            )
            .filter(
                Deal.workspace_id == self.workspace_id,
                Deal.deleted_at.is_(None),
                Deal.stage == DealStage.WON,
                Deal.won_at >= since,
            )
            .group_by(func.date(Deal.won_at))
            .order_by(func.date(Deal.won_at))
            .all()
        )
        return [{"date": str(r.date), "revenue": float(r.revenue or 0), "count": int(r.count)} for r in rows]
