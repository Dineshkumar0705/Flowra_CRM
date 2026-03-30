"""Automation routes — stale deal scan, autopilot trigger."""

from fastapi import APIRouter, status

from app.api.deps import AdminDep, CurrentUserDep, DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.services.automation_service import AutomationService

router = APIRouter()


@router.post("/stale-deals/scan", response_model=SuccessResponse[dict])
def scan_stale_deals(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """
    Scan for deals with no activity in 3+ days and send follow-up notifications.
    Requires admin/owner.
    """
    svc = AutomationService(db, workspace_id)
    flagged = svc.check_stale_deals()
    return success(
        {"flagged_count": len(flagged), "deal_ids": flagged},
        message=f"{len(flagged)} stale deal(s) flagged.",
    )


@router.post("/autopilot/{deal_id}", response_model=SuccessResponse[dict])
def trigger_autopilot(
    deal_id: str,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """
    Manually trigger the onboarding autopilot for a specific deal.
    Useful for re-running failed automations.
    """
    from app.repositories.deal_repo import DealRepository
    from app.core.exceptions import NotFoundError

    repo = DealRepository(db, workspace_id)
    deal = repo.get_by_id(deal_id)
    if not deal:
        raise NotFoundError("Deal", deal_id)

    from app.services.onboarding_autopilot import OnboardingAutopilot
    pilot = OnboardingAutopilot(db, workspace_id)
    summary = pilot.run(deal, user_id=current_user.id)
    return success(summary, message="Autopilot executed.")
