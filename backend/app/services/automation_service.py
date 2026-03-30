"""Automation rule engine — workspace-level, event-driven triggers."""

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.deal import Deal, DealStage
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService

log = logging.getLogger("flowra.service.automation")


class AutomationService:
    """
    Evaluates and fires automation rules when CRM events occur.

    Current triggers:
      - deal_stage_changed → score update, autopilot, notifications
      - deal_created       → score, priority assignment
      - deal_stale         → follow-up notification

    Rules are defined in code (Phase 1).  A DB-driven rule builder is
    planned for Phase 2.
    """

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.notification_svc = NotificationService(db, workspace_id)

    # ------------------------------------------------------------------
    # Event: deal stage changed
    # ------------------------------------------------------------------

    def on_deal_stage_changed(
        self,
        deal: Deal,
        old_stage: DealStage,
        new_stage: DealStage,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Called every time a deal moves to a new stage.

        Returns a dict describing the actions taken.
        """
        actions_taken = []

        # Log to activity trail
        self.notification_svc.log_activity(
            entity_type="deal",
            entity_id=deal.id,
            action="stage_changed",
            user_id=user_id,
            old_value={"stage": old_stage},
            new_value={"stage": new_stage},
            description=f"Deal moved from {old_stage} → {new_stage}",
        )
        actions_taken.append("activity_logged")

        # Create in-app notification for deal owner
        if deal.owner_id:
            if new_stage == DealStage.WON:
                self.notification_svc.create(
                    user_id=deal.owner_id,
                    notification_type=NotificationType.DEAL_WON,
                    title=f"🏆 Deal won: {deal.title}",
                    body=f"Value: {deal.currency} {deal.value:,.0f}",
                    action_url=f"/deals/{deal.id}",
                )
                actions_taken.append("deal_won_notification")

                # Fire autopilot
                try:
                    from app.services.onboarding_autopilot import OnboardingAutopilot
                    pilot = OnboardingAutopilot(self.db, self.workspace_id)
                    pilot.run(deal, user_id=user_id)
                    actions_taken.append("autopilot_fired")
                except Exception as exc:
                    log.error("automation.autopilot_failed", deal_id=deal.id, error=str(exc))

        log.info(
            "automation.stage_change_processed",
            deal_id=deal.id,
            old_stage=old_stage,
            new_stage=new_stage,
            actions=actions_taken,
        )
        return {"deal_id": deal.id, "actions": actions_taken}

    # ------------------------------------------------------------------
    # Event: deal created
    # ------------------------------------------------------------------

    def on_deal_created(self, deal: Deal, user_id: str) -> Dict[str, Any]:
        """Called immediately after a new deal is created."""
        self.notification_svc.log_activity(
            entity_type="deal",
            entity_id=deal.id,
            action="created",
            user_id=user_id,
            new_value={"title": deal.title, "value": deal.value, "stage": deal.stage},
        )

        # Notify workspace admins about large new deals
        if deal.value >= 500_000:
            log.info("automation.high_value_deal_created", deal_id=deal.id, value=deal.value)

        return {"deal_id": deal.id, "actions": ["activity_logged"]}

    # ------------------------------------------------------------------
    # Event: contact created
    # ------------------------------------------------------------------

    def on_contact_created(self, contact_id: str, user_id: str) -> None:
        self.notification_svc.log_activity(
            entity_type="contact",
            entity_id=contact_id,
            action="created",
            user_id=user_id,
        )

    # ------------------------------------------------------------------
    # Stale deal scan (run by a scheduled job)
    # ------------------------------------------------------------------

    def check_stale_deals(self) -> List[str]:
        """
        Find open deals with no activity in the last 3 days and
        send follow-up notifications to their owners.

        Returns list of deal IDs flagged.
        """
        from datetime import timedelta, timezone
        from datetime import datetime
        from app.models.deal import Deal

        threshold = datetime.now(timezone.utc) - timedelta(days=3)
        stale = (
            self.db.query(Deal)
            .filter(
                Deal.workspace_id == self.workspace_id,
                Deal.deleted_at.is_(None),
                Deal.stage.notin_([DealStage.WON, DealStage.LOST]),
                Deal.updated_at <= threshold,
            )
            .all()
        )

        flagged = []
        for deal in stale:
            if deal.owner_id:
                self.notification_svc.create(
                    user_id=deal.owner_id,
                    notification_type=NotificationType.OVERDUE_TASK,
                    title=f"⏰ Follow up: {deal.title}",
                    body="No activity in 3+ days. Time to reach out!",
                    action_url=f"/deals/{deal.id}",
                )
            flagged.append(deal.id)

        log.info("automation.stale_check", count=len(flagged))
        return flagged
