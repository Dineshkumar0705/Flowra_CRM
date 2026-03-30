"""Notification and ActivityLog schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.notification import NotificationType
from app.schemas.base import FlowraSchema


class NotificationResponse(FlowraSchema):
    id: str
    workspace_id: str
    user_id: str
    notification_type: NotificationType
    title: str
    body: Optional[str] = None
    action_url: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None
    read_at: Optional[datetime] = None
    is_read: bool
    created_at: datetime


class MarkReadRequest(FlowraSchema):
    notification_ids: List[str]


class ActivityLogResponse(FlowraSchema):
    id: str
    workspace_id: str
    user_id: Optional[str] = None
    entity_type: str
    entity_id: Optional[str] = None
    action: str
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


# Aliases
NotificationOut = NotificationResponse
ActivityLogOut = ActivityLogResponse
