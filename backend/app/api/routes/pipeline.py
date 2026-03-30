"""Pipeline routes — pipeline CRUD, stage management, Kanban board."""

from typing import List

from fastapi import APIRouter, status

from app.api.deps import AdminDep, DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.core.exceptions import NotFoundError
from app.schemas.base import SuccessResponse, success
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineResponse,
    StageCreate,
    StageResponse,
    PipelineUpdate,
    StageUpdate,
)
from app.services.pipeline_service import PipelineService

router = APIRouter()


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------


@router.get("", response_model=SuccessResponse[List[PipelineResponse]])
def list_pipelines(workspace_id: WorkspaceIdDep, db: DbDep, _member: WorkspaceMemberDep):
    """List all pipelines in the workspace."""
    svc = PipelineService(db, workspace_id)
    pipelines = svc.list_pipelines()
    return success([PipelineResponse.model_validate(p) for p in pipelines])


@router.post("", response_model=SuccessResponse[PipelineResponse], status_code=status.HTTP_201_CREATED)
def create_pipeline(
    payload: PipelineCreate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Create a new pipeline. Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    pipeline = svc.create_pipeline(payload)
    return success(PipelineResponse.model_validate(pipeline), message="Pipeline created.")


@router.get("/{pipeline_id}", response_model=SuccessResponse[PipelineResponse])
def get_pipeline(
    pipeline_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Get a pipeline by ID."""
    svc = PipelineService(db, workspace_id)
    pipeline = svc.get_pipeline(pipeline_id)
    if not pipeline:
        raise NotFoundError("Pipeline", pipeline_id)
    return success(PipelineResponse.model_validate(pipeline))


@router.patch("/{pipeline_id}", response_model=SuccessResponse[PipelineResponse])
def update_pipeline(
    pipeline_id: str,
    payload: PipelineUpdate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Update a pipeline. Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    pipeline = svc.update_pipeline(pipeline_id, payload)
    return success(PipelineResponse.model_validate(pipeline), message="Pipeline updated.")


@router.delete("/{pipeline_id}", response_model=SuccessResponse[None])
def delete_pipeline(
    pipeline_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Delete a pipeline (soft). Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    svc.delete_pipeline(pipeline_id)
    return success(None, message="Pipeline deleted.")


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------


@router.get("/{pipeline_id}/stages", response_model=SuccessResponse[List[StageResponse]])
def list_stages(
    pipeline_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """List all stages for a pipeline."""
    svc = PipelineService(db, workspace_id)
    stages = svc.list_stages(pipeline_id)
    return success([StageResponse.model_validate(s) for s in stages])


@router.post("/{pipeline_id}/stages", response_model=SuccessResponse[StageResponse], status_code=status.HTTP_201_CREATED)
def create_stage(
    pipeline_id: str,
    payload: StageCreate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Add a stage to a pipeline. Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    stage = svc.create_stage(pipeline_id, payload)
    return success(StageResponse.model_validate(stage), message="Stage created.")


@router.patch("/{pipeline_id}/stages/{stage_id}", response_model=SuccessResponse[StageResponse])
def update_stage(
    pipeline_id: str,
    stage_id: str,
    payload: StageUpdate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Update a pipeline stage. Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    stage = svc.update_stage(stage_id, payload)
    return success(StageResponse.model_validate(stage), message="Stage updated.")


@router.delete("/{pipeline_id}/stages/{stage_id}", response_model=SuccessResponse[None])
def delete_stage(
    pipeline_id: str,
    stage_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Delete a pipeline stage. Requires admin/owner."""
    svc = PipelineService(db, workspace_id)
    svc.delete_stage(stage_id)
    return success(None, message="Stage deleted.")


# ---------------------------------------------------------------------------
# Kanban board
# ---------------------------------------------------------------------------


@router.get("/{pipeline_id}/board", response_model=SuccessResponse[dict])
def get_board(
    pipeline_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the full Kanban board with deals grouped by stage."""
    svc = PipelineService(db, workspace_id)
    board = svc.get_board(pipeline_id)
    return success(board)
