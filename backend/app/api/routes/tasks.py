"""Tasks routes — full CRUD + complete action + summary."""

from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUserDep, DbDep, PaginationDep, WorkspaceIdDep, WorkspaceMemberDep
from app.core.exceptions import NotFoundError
from app.models.task import TaskPriority, TaskStatus
from app.schemas.base import PaginatedResponse, SuccessResponse, paginated, success
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TaskResponse])
def list_tasks(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    pagination: PaginationDep,
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str]      = Query(None),
    assigned_to: Optional[str]   = Query(None),
    contact_id: Optional[str]    = Query(None),
    deal_id: Optional[str]       = Query(None),
    overdue_only: bool            = Query(False),
):
    """List tasks with optional filters."""
    svc = TaskService(db, workspace_id)
    items, total = svc.list(
        page=pagination.page,
        per_page=pagination.limit,
        status=TaskStatus(status_filter) if status_filter else None,
        priority=TaskPriority(priority) if priority else None,
        assigned_to=assigned_to,
        contact_id=contact_id,
        deal_id=deal_id,
        overdue_only=overdue_only,
    )
    return paginated(
        [TaskResponse.model_validate(t) for t in items],
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
    )


@router.post("", response_model=SuccessResponse[TaskResponse], status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Create a new task."""
    svc  = TaskService(db, workspace_id)
    task = svc.create(payload, created_by=current_user.id)
    return success(TaskResponse.model_validate(task), message="Task created.")


@router.get("/summary", response_model=SuccessResponse[dict])
def task_summary(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return task counts by status + overdue count."""
    svc = TaskService(db, workspace_id)
    return success(svc.summary())


@router.get("/{task_id}", response_model=SuccessResponse[TaskResponse])
def get_task(
    task_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Get a single task by ID."""
    svc  = TaskService(db, workspace_id)
    task = svc.get(task_id)
    if not task:
        raise NotFoundError("Task", task_id)
    return success(TaskResponse.model_validate(task))


@router.patch("/{task_id}", response_model=SuccessResponse[TaskResponse])
def update_task(
    task_id: str,
    payload: TaskUpdate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Partially update a task."""
    svc  = TaskService(db, workspace_id)
    task = svc.update(task_id, payload)
    return success(TaskResponse.model_validate(task), message="Task updated.")


@router.post("/{task_id}/complete", response_model=SuccessResponse[TaskResponse])
def complete_task(
    task_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Mark a task as done and stamp completed_at."""
    svc  = TaskService(db, workspace_id)
    task = svc.complete(task_id)
    return success(TaskResponse.model_validate(task), message="Task completed.")


@router.delete("/{task_id}", response_model=SuccessResponse[None])
def delete_task(
    task_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Soft-delete a task."""
    svc = TaskService(db, workspace_id)
    svc.delete(task_id)
    return success(None, message="Task deleted.")
