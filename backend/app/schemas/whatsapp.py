"""WhatsApp schema: API requests/responses and webhook payloads."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.whatsapp_message import MessageDirection, MessageStatus, MessageType
from app.schemas.base import FlowraSchema


# ---------------------------------------------------------------------------
# Outbound (CRM → Contact)
# ---------------------------------------------------------------------------

class SendTextMessageRequest(FlowraSchema):
    to_number: str = Field(..., description="E.164 phone number, e.g. +919876543210")
    body: str = Field(..., min_length=1, max_length=4096)
    contact_id: Optional[str] = None   # if known, link to contact


class SendTemplateMessageRequest(FlowraSchema):
    to_number: str = Field(..., description="E.164 phone number")
    template_name: str = Field(..., min_length=1)
    language_code: str = Field(default="en_US")
    components: List[Dict[str, Any]] = Field(default_factory=list)
    contact_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Inbound webhook payload (Meta Cloud API)
# ---------------------------------------------------------------------------

class WAMessage(FlowraSchema):
    id: str
    from_: str = Field(alias="from")
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None

    class Config:
        populate_by_name = True


class WAContact(FlowraSchema):
    profile: Optional[Dict[str, str]] = None
    wa_id: str


class WAValue(FlowraSchema):
    messaging_product: str
    metadata: Dict[str, str]
    contacts: Optional[List[WAContact]] = None
    messages: Optional[List[WAMessage]] = None
    statuses: Optional[List[Dict[str, Any]]] = None


class WAChange(FlowraSchema):
    value: WAValue
    field: str


class WAEntry(FlowraSchema):
    id: str
    changes: List[WAChange]


class WhatsAppWebhookPayload(FlowraSchema):
    object: str
    entry: List[WAEntry]


# ---------------------------------------------------------------------------
# DB row response
# ---------------------------------------------------------------------------

class WhatsAppMessageResponse(FlowraSchema):
    id: str
    workspace_id: str
    contact_id: Optional[str] = None
    wa_message_id: Optional[str] = None
    direction: MessageDirection
    message_type: MessageType
    status: MessageStatus
    from_number: str
    to_number: str
    body: Optional[str] = None
    media_url: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime


# Aliases
WhatsAppMessageOut = WhatsAppMessageResponse
SendTextRequest = SendTextMessageRequest
SendTemplateRequest = SendTemplateMessageRequest
