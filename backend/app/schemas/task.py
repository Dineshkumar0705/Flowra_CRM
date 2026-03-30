"""Task Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.models.task import TaskPriority, TaskStatus
from app.schemas.base import FlowraSchema


class TaskCreate(FlowraSchema):
    title:       str            = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    status:      TaskStatus     = TaskStatus.TODO
    priority:    TaskPriority   = TaskPriority.MEDIUM
    due_at:      Optional[datetime] = None
    contact_id:  Optional[str] = None
    deal_id:     Optional[str] = None
    assigned_to: Optional[str] = None


class TaskUpdate(FlowraSchema):
    title:       Optional[str]         = Field(None, min_length=1, max_length=500)
    description: Optional[str]         = None
    status:      Optional[TaskStatus]  = None
    priority:    Optional[TaskPriority] = None
    due_at:      Optional[datetime]    = None
    contact_id:  Optional[str]         = None
    deal_id:     Optional[str]         = None
    assigned_to: Optional[str]         = None


class TaskResponse(FlowraSchema):
    id:           str
    workspace_id: str
    title:        str
    description:  Optional[str]   = None
    status:       TaskStatus
    priority:     TaskPriority
    due_at:       Optional[datetime] = None
    completed_at: Optional[datetime] = None
    contact_id:   Optional[str]   = None
    deal_id:      Optional[str]   = None
    assigned_to:  Optional[str]   = None
    created_by:   Optional[str]   = None
    is_overdue:   bool            = False
    created_at:   datetime
    updated_at:   datetime


# Alias
TaskOut = TaskResponse
