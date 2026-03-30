"""Analytics service — dashboard KPIs and revenue forecasting."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.deal import Deal, DealStage
from app.repositories.deal_repo import DealRepository
from app.repositories.pipeline_repo import PipelineRepository

log = logging.getLogger("flowra.service.analytics")


class AnalyticsService:
    """
    Business logic for CRM analytics.

    All heavy-lifting is done at the DB level (SQL aggregations) rather than
    in Python, so this scales to millions of deals without memory issues.
    """

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.deal_repo = DealRepository(db, workspace_id)

    # ------------------------------------------------------------------
    # Master dashboard
    # ------------------------------------------------------------------

    def get_full_dashboard(self) -> Dict[str, Any]:
        return {
            "summary": self._summary(),
            "stage_distribution": self.deal_repo.stage_distribution(),
            "revenue_trend_30d": self._revenue_trend(30),
            "top_deals": self._top_deals(5),
            "conversion": self._conversion_metrics(),
            "forecast": self._forecast(),
        }

    # ------------------------------------------------------------------
    # Summary KPIs
    # ------------------------------------------------------------------

    def _summary(self) -> Dict[str, Any]:
        total = self.deal_repo.total_value()
        pipeline = self.deal_repo.pipeline_value()
        win_rate = self.deal_repo.win_rate()

        # Total deal count
        deal_count = (
            self.db.query(func.count(Deal.id))
            .filter(Deal.workspace_id == self.workspace_id, Deal.deleted_at.is_(None))
            .scalar()
        ) or 0

        avg_deal_size = round(total / deal_count, 2) if deal_count else 0

        return {
            "total_revenue": round(total, 2),
            "pipeline_value": round(pipeline, 2),
            "total_deals": deal_count,
            "avg_deal_size": avg_deal_size,
            "win_rate": win_rate,
        }

    # ------------------------------------------------------------------
    # Revenue trend (time series)
    # ------------------------------------------------------------------

    def _revenue_trend(self, days: int) -> List[Dict[str, Any]]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return self.deal_repo.revenue_by_date(since)

    # ------------------------------------------------------------------
    # Top deals
    # ------------------------------------------------------------------

    def _top_deals(self, limit: int = 5) -> List[Dict[str, Any]]:
        deals = self.deal_repo.top_deals(limit)
        return [
            {
                "id": d.id,
                "title": d.title,
                "value": d.value,
                "stage": d.stage,
                "probability": d.probability,
                "ai_score": d.ai_score,
            }
            for d in deals
        ]

    # ------------------------------------------------------------------
    # Conversion metrics
    # ------------------------------------------------------------------

    def _conversion_metrics(self) -> Dict[str, Any]:
        dist = self.deal_repo.stage_distribution()
        total = sum(dist.values())
        won = dist.get(DealStage.WON, 0)
        lost = dist.get(DealStage.LOST, 0)

        return {
            "total_deals": total,
            "won": won,
            "lost": lost,
            "win_rate": round((won / total * 100) if total else 0, 2),
            "loss_rate": round((lost / total * 100) if total else 0, 2),
            "in_progress": total - won - lost,
        }

    # ------------------------------------------------------------------
    # Revenue forecast
    # ------------------------------------------------------------------

    def _forecast(self) -> Dict[str, Any]:
        return {
            "expected_revenue": round(self.deal_repo.pipeline_value(), 2),
            "explanation": "Sum of (deal_value × probability) for all open deals.",
        }

    # ------------------------------------------------------------------
    # Stale deal alerts
    # ------------------------------------------------------------------

    def get_stale_deals_summary(self, days_inactive: int = 3) -> Dict[str, Any]:
        threshold = datetime.now(timezone.utc) - timedelta(days=days_inactive)
        count = (
            self.db.query(func.count(Deal.id))
            .filter(
                Deal.workspace_id == self.workspace_id,
                Deal.deleted_at.is_(None),
                Deal.stage.notin_([DealStage.WON, DealStage.LOST]),
                Deal.updated_at <= threshold,
            )
            .scalar()
        ) or 0
        return {"stale_deal_count": count, "threshold_days": days_inactive}
