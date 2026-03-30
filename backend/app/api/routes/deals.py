"""Deal routes — CRUD, stage moves, dashboard."""

from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUserDep,
    DbDep,
    PaginationDep,
    WorkspaceIdDep,
    WorkspaceMemberDep,
)
from app.core.exceptions import NotFoundError
from app.schemas.base import PaginatedResponse, SuccessResponse, paginated, success
from app.schemas.deal import DealCreate, DealFilters, DealResponse, DealStageMove, DealUpdate
from app.services.deal_service import DealService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DealResponse])
def list_deals(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    pagination: PaginationDep,
    stage: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    contact_id: Optional[str] = Query(None),
    pipeline_id: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
):
    """List deals with optional filters."""
    svc = DealService(db, workspace_id)
    filters = DealFilters(
        stage=stage,
        priority=priority,
        owner_id=owner_id,
        contact_id=contact_id,
        pipeline_id=pipeline_id,
        min_value=min_value,
        max_value=max_value,
        search=search,
    )
    items, total = svc.list(
        filters=filters,
        page=pagination.page,
        per_page=pagination.limit,
    )
    return paginated(
        [DealResponse.model_validate(d) for d in items],
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
    )


@router.post("", response_model=SuccessResponse[DealResponse], status_code=status.HTTP_201_CREATED)
def create_deal(
    payload: DealCreate,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Create a new deal."""
    svc = DealService(db, workspace_id)
    deal = svc.create(payload, created_by=current_user.id)
    return success(DealResponse.model_validate(deal), message="Deal created.")


@router.get("/dashboard", response_model=SuccessResponse[dict])
def get_dashboard(workspace_id: WorkspaceIdDep, db: DbDep, _member: WorkspaceMemberDep):
    """Return KPI summary for the deals dashboard."""
    svc = DealService(db, workspace_id)
    data = svc.get_dashboard()
    return success(data)


@router.get("/{deal_id}", response_model=SuccessResponse[DealResponse])
def get_deal(
    deal_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Get a single deal by ID."""
    svc = DealService(db, workspace_id)
    deal = svc.get(deal_id)
    if not deal:
        raise NotFoundError("Deal", deal_id)
    return success(DealResponse.model_validate(deal))


@router.patch("/{deal_id}", response_model=SuccessResponse[DealResponse])
def update_deal(
    deal_id: str,
    payload: DealUpdate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Partially update a deal's fields."""
    svc = DealService(db, workspace_id)
    deal = svc.update(deal_id, payload)
    return success(DealResponse.model_validate(deal), message="Deal updated.")


@router.delete("/{deal_id}", response_model=SuccessResponse[None])
def delete_deal(
    deal_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Soft-delete a deal."""
    svc = DealService(db, workspace_id)
    svc.delete(deal_id)
    return success(None, message="Deal deleted.")


@router.post("/{deal_id}/move-stage", response_model=SuccessResponse[DealResponse])
def move_stage(
    deal_id: str,
    payload: DealStageMove,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Move a deal to a different pipeline stage."""
    svc = DealService(db, workspace_id)
    deal = svc.move_stage(deal_id, payload.stage)
    return success(DealResponse.model_validate(deal), message=f"Deal moved to {payload.stage}.")
