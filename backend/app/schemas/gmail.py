"""Gmail integration Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.schemas.base import FlowraSchema


class GmailIntegrationOut(FlowraSchema):
    id: str
    workspace_id: str
    user_id: str
    google_email: Optional[str] = None
    is_active: bool
    last_sync_at: Optional[datetime] = None
    synced_messages_count: int = 0
    created_at: datetime


class EmailMessageOut(FlowraSchema):
    id: str
    workspace_id: str
    contact_id: Optional[str] = None
    direction: str
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    subject: Optional[str] = None
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    tracking_pixel_id: Optional[str] = None
    open_count: int = 0
    first_opened_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class SendEmailRequest(FlowraSchema):
    to_email: EmailStr
    subject: str = Field(..., min_length=1, max_length=998)
    body_html: str = Field(..., min_length=1)
    contact_id: Optional[str] = None
