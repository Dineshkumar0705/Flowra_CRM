"""
Task service — business logic for creating, listing, updating, and completing tasks.

All queries are workspace-scoped (workspace_id is injected at construction time).
"""

from datetime import datetime, timezone
from typing import Optional, Tuple, List

from sqlalchemy import and_, or_, asc, desc
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db           = db
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base_query(self):
        """Return a query scoped to this workspace, excluding soft-deleted rows."""
        return (
            self.db.query(Task)
            .filter(
                Task.workspace_id == self.workspace_id,
                Task.deleted_at.is_(None),
            )
        )

    def _get_or_raise(self, task_id: str) -> Task:
        task = self._base_query().filter(Task.id == task_id).first()
        if not task:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Task", task_id)
        return task

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, payload: TaskCreate, created_by: Optional[str] = None) -> Task:
        task = Task(
            workspace_id = self.workspace_id,
            title        = payload.title,
            description  = payload.description,
            status       = payload.status,
            priority     = payload.priority,
            due_at       = payload.due_at,
            contact_id   = payload.contact_id,
            deal_id      = payload.deal_id,
            assigned_to  = payload.assigned_to,
            created_by   = created_by,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get(self, task_id: str) -> Optional[Task]:
        return self._base_query().filter(Task.id == task_id).first()

    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        assigned_to: Optional[str] = None,
        contact_id: Optional[str] = None,
        deal_id: Optional[str] = None,
        overdue_only: bool = False,
    ) -> Tuple[List[Task], int]:
        q = self._base_query()

        if status:
            q = q.filter(Task.status == status)
        if priority:
            q = q.filter(Task.priority == priority)
        if assigned_to:
            q = q.filter(Task.assigned_to == assigned_to)
        if contact_id:
            q = q.filter(Task.contact_id == contact_id)
        if deal_id:
            q = q.filter(Task.deal_id == deal_id)
        if overdue_only:
            now = datetime.now(timezone.utc)
            q = q.filter(
                Task.due_at < now,
                Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
            )

        # Sort: overdue first, then by due_at asc, then created_at desc
        q = q.order_by(
            asc(Task.due_at.is_(None)),
            asc(Task.due_at),
            desc(Task.created_at),
        )

        total  = q.count()
        offset = (page - 1) * per_page
        items  = q.offset(offset).limit(per_page).all()
        return items, total

    def update(self, task_id: str, payload: TaskUpdate) -> Task:
        task = self._get_or_raise(task_id)
        data = payload.model_dump(exclude_unset=True)

        # If status is transitioning to DONE, stamp completed_at
        if "status" in data and data["status"] == TaskStatus.DONE and task.status != TaskStatus.DONE:
            data["completed_at"] = datetime.now(timezone.utc)

        # If status is moving away from DONE, clear completed_at
        if "status" in data and data["status"] != TaskStatus.DONE and task.status == TaskStatus.DONE:
            data["completed_at"] = None

        for field, value in data.items():
            setattr(task, field, value)

        self.db.commit()
        self.db.refresh(task)
        return task

    def complete(self, task_id: str) -> Task:
        task = self._get_or_raise(task_id)
        task.status       = TaskStatus.DONE
        task.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: str) -> None:
        task = self._get_or_raise(task_id)
        task.soft_delete()
        self.db.commit()

    # ------------------------------------------------------------------
    # Dashboard summary
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """Return counts by status + overdue count for the dashboard widget."""
        q    = self._base_query()
        now  = datetime.now(timezone.utc)
        total    = q.count()
        todo     = q.filter(Task.status == TaskStatus.TODO).count()
        in_prog  = q.filter(Task.status == TaskStatus.IN_PROGRESS).count()
        done     = q.filter(Task.status == TaskStatus.DONE).count()
        overdue  = q.filter(
            Task.due_at < now,
            Task.status.notin_([TaskStatus.DONE, TaskStatus.CANCELLED]),
        ).count()
        return {
            "total":       total,
            "todo":        todo,
            "in_progress": in_prog,
            "done":        done,
            "overdue":     overdue,
        }
