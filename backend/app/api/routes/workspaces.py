"""Workspace routes — CRUD and member management."""

from typing import List, Optional

from fastapi import APIRouter, Query, status

from app.api.deps import (
    AdminDep,
    CurrentUserDep,
    DbDep,
    OwnerDep,
    PaginationDep,
    WorkspaceIdDep,
    WorkspaceMemberDep,
)
from app.schemas.base import PaginatedResponse, SuccessResponse, paginated, success
from app.schemas.workspace import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
    UpdateWorkspaceRequest,
    WorkspaceMemberOut,
    WorkspaceOut,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter()


@router.get("", response_model=SuccessResponse[List[WorkspaceOut]])
def list_my_workspaces(current_user: CurrentUserDep, db: DbDep):
    """List all workspaces the current user belongs to."""
    svc = WorkspaceService(db)
    items = svc.list_for_user(current_user.id)
    return success([WorkspaceOut.model_validate(w) for w in items])


@router.get("/current", response_model=SuccessResponse[WorkspaceOut])
def get_current_workspace(workspace_id: WorkspaceIdDep, db: DbDep, _member: WorkspaceMemberDep):
    """Return details of the current workspace (from JWT)."""
    svc = WorkspaceService(db)
    ws = svc.get_or_raise(workspace_id)
    return success(WorkspaceOut.model_validate(ws))


@router.patch("/current", response_model=SuccessResponse[WorkspaceOut])
def update_workspace(
    payload: UpdateWorkspaceRequest,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Update workspace name or settings. Requires admin/owner."""
    svc = WorkspaceService(db)
    ws = svc.update(workspace_id, payload)
    return success(WorkspaceOut.model_validate(ws))


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@router.get("/current/members", response_model=SuccessResponse[List[WorkspaceMemberOut]])
def list_members(workspace_id: WorkspaceIdDep, db: DbDep, _member: WorkspaceMemberDep):
    """List all members in the current workspace."""
    svc = WorkspaceService(db)
    members = svc.list_members(workspace_id)
    return success([WorkspaceMemberOut.model_validate(m) for m in members])


@router.post("/current/members", response_model=SuccessResponse[WorkspaceMemberOut], status_code=status.HTTP_201_CREATED)
def add_member(
    payload: AddMemberRequest,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Invite a user to the workspace by email. Requires admin/owner."""
    svc = WorkspaceService(db)
    member = svc.add_member(workspace_id, payload)
    return success(WorkspaceMemberOut.model_validate(member), message="Member added.")


@router.patch("/current/members/{user_id}", response_model=SuccessResponse[WorkspaceMemberOut])
def update_member_role(
    user_id: str,
    payload: UpdateMemberRoleRequest,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _owner: OwnerDep,
):
    """Change a member's role. Requires owner."""
    svc = WorkspaceService(db)
    member = svc.update_member_role(workspace_id, user_id, payload.role)
    return success(WorkspaceMemberOut.model_validate(member))


@router.delete("/current/members/{user_id}", response_model=SuccessResponse[None])
def remove_member(
    user_id: str,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _owner: OwnerDep,
):
    """Remove a member from the workspace. Requires owner."""
    svc = WorkspaceService(db)
    svc.remove_member(workspace_id, user_id)
    return success(None, message="Member removed.")
