"""Analytics routes — dashboard KPIs and revenue trends."""

from fastapi import APIRouter, Query

from app.api.deps import DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=SuccessResponse[dict])
def get_full_dashboard(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return comprehensive dashboard: KPIs, stage dist, revenue trend, top deals, forecast."""
    svc = AnalyticsService(db, workspace_id)
    data = svc.get_full_dashboard()
    return success(data)


@router.get("/revenue", response_model=SuccessResponse[dict])
def get_revenue_trend(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    days: int = Query(30, ge=7, le=365, description="Lookback window in days"),
):
    """Return daily revenue trend for won deals."""
    svc = AnalyticsService(db, workspace_id)
    # _revenue_trend is exposed via get_full_dashboard; call it directly for isolated use
    data = svc._revenue_trend(days=days)
    return success({"days": days, "trend": data})


@router.get("/conversion", response_model=SuccessResponse[dict])
def get_conversion_metrics(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return win/loss rates and conversion funnel metrics."""
    svc = AnalyticsService(db, workspace_id)
    data = svc._conversion_metrics()
    return success(data)


@router.get("/forecast", response_model=SuccessResponse[dict])
def get_forecast(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return weighted pipeline value forecast."""
    svc = AnalyticsService(db, workspace_id)
    data = svc._forecast()
    return success(data)
