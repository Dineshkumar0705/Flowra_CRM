"""Deal CRUD service with stage-transition hooks."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.deal import Deal, DealPriority, DealStage
from app.repositories.deal_repo import DealRepository
from app.schemas.deal import DealCreate, DealFilters, DealUpdate

log = logging.getLogger("flowra.service.deal")


class DealService:
    """Business logic for Deal management."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.repo = DealRepository(db, workspace_id)
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, payload: DealCreate, created_by: Optional[str] = None) -> Deal:
        """Create a new deal and run initial automation scoring."""
        data = payload.model_dump(exclude_unset=False)
        data["created_by"] = created_by
        deal = self.repo.create(data)
        deal = self._run_auto_score(deal)
        log.info("deal.created", workspace=self.workspace_id, deal_id=deal.id, value=deal.value)
        return deal

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, deal_id: str) -> Deal:
        deal = self.repo.get_by_id(deal_id)
        if not deal:
            raise NotFoundError("Deal", deal_id)
        return deal

    def list(
        self,
        filters: DealFilters,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Deal], int]:
        skip = (page - 1) * per_page
        return self.repo.list(
            skip=skip,
            limit=per_page,
            stage=filters.stage,
            priority=filters.priority,
            owner_id=filters.owner_id,
            contact_id=filters.contact_id,
            pipeline_id=filters.pipeline_id,
            search=filters.search,
            min_value=filters.min_value,
            max_value=filters.max_value,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, deal_id: str, payload: DealUpdate) -> Deal:
        deal = self.get(deal_id)
        data = payload.model_dump(exclude_unset=True)

        if "stage" in data:
            new_stage = DealStage(data.pop("stage"))
            deal = self.repo.move_stage(deal, new_stage)
            self._on_stage_changed(deal, new_stage)

        if data:
            deal = self.repo.update(deal, data)
            deal = self._run_auto_score(deal)

        return deal

    # ------------------------------------------------------------------
    # Stage transition
    # ------------------------------------------------------------------

    def move_stage(self, deal_id: str, new_stage: DealStage) -> Deal:
        """Move a deal to a new stage and trigger automation."""
        deal = self.get(deal_id)
        old_stage = deal.stage
        deal = self.repo.move_stage(deal, new_stage)
        self._on_stage_changed(deal, new_stage)
        log.info(
            "deal.stage_changed",
            deal_id=deal_id, old_stage=old_stage, new_stage=new_stage,
            workspace=self.workspace_id,
        )
        return deal

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, deal_id: str) -> None:
        deal = self.get(deal_id)
        self.repo.soft_delete(deal)
        log.info("deal.deleted", deal_id=deal_id)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_dashboard(self) -> Dict[str, Any]:
        return {
            "total_value": self.repo.total_value(),
            "pipeline_value": self.repo.pipeline_value(),
            "win_rate": self.repo.win_rate(),
            "stage_distribution": self.repo.stage_distribution(),
            "top_deals": [
                {"id": d.id, "title": d.title, "value": d.value}
                for d in self.repo.top_deals(5)
            ],
        }

    def get_revenue_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return self.repo.revenue_by_date(since)

    def get_stale_deals(self, days_inactive: int = 3) -> List[Deal]:
        threshold = datetime.now(timezone.utc) - timedelta(days=days_inactive)
        items, _ = self.repo.list(limit=200)
        return [
            d for d in items
            if d.is_open and d.updated_at
            and d.updated_at.replace(tzinfo=timezone.utc) < threshold
        ]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_auto_score(self, deal: Deal) -> Deal:
        """Rule-based AI scoring — zero external API calls."""
        score = 0.0
        if deal.value >= 500_000:
            score += 50
        elif deal.value >= 200_000:
            score += 35
        elif deal.value >= 100_000:
            score += 25
        elif deal.value >= 50_000:
            score += 15
        else:
            score += 5

        stage_weight = {
            DealStage.NEW: 5, DealStage.CONTACTED: 15, DealStage.QUALIFIED: 25,
            DealStage.PROPOSAL: 35, DealStage.NEGOTIATION: 45,
            DealStage.WON: 50, DealStage.LOST: 0,
        }
        score += stage_weight.get(deal.stage, 0)
        deal.ai_score = min(score, 100.0)

        if deal.value >= 200_000 and deal.priority == DealPriority.LOW:
            deal.priority = DealPriority.MEDIUM

        self.db.commit()
        self.db.refresh(deal)
        return deal

    def _on_stage_changed(self, deal: Deal, new_stage: DealStage) -> None:
        notes_map = {
            DealStage.NEW: "New deal. Assign an owner and qualify quickly.",
            DealStage.CONTACTED: "First contact made. Schedule a follow-up call.",
            DealStage.QUALIFIED: "Qualified. Confirm budget, authority, need, timeline.",
            DealStage.PROPOSAL: "Proposal sent. Follow up within 48 hours.",
            DealStage.NEGOTIATION: "Negotiating. Anchor on value, not price.",
            DealStage.WON: "🎉 Deal closed! Onboarding autopilot should fire now.",
            DealStage.LOST: "Deal lost. Document the loss reason for future learning.",
        }
        deal.ai_notes = notes_map.get(new_stage, "")
        self.db.commit()
