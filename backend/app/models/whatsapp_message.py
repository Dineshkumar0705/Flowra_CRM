"""
WhatsApp message model.

Stores all inbound and outbound WhatsApp Business Cloud API messages.
Messages are linked to Contacts by phone number on receipt.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class MessageDirection(str, enum.Enum):
    INBOUND = "inbound"     # received from contact
    OUTBOUND = "outbound"   # sent by CRM user


class MessageType(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"


class MessageStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class WhatsAppMessage(TimestampMixin, Base):
    """
    A single WhatsApp message (inbound or outbound).

    Meta's Cloud API sends webhook events for delivery receipts — we
    update the status column when those arrive.
    """

    __tablename__ = "whatsapp_messages"

    # ------------------------------------------------------------------
    # Multi-tenancy
    # ------------------------------------------------------------------
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Contact link (nullable — set once the number is matched to a contact)
    # ------------------------------------------------------------------
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Message data
    # ------------------------------------------------------------------
    wa_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True, index=True)
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection), nullable=False, index=True
    )
    message_type: Mapped[MessageType] = mapped_column(
        Enum(MessageType), default=MessageType.TEXT, nullable=False
    )
    status: Mapped[MessageStatus] = mapped_column(
        Enum(MessageStatus), default=MessageStatus.QUEUED, nullable=False, index=True
    )

    # Phone numbers (always store in E.164 format, e.g. "+919876543210")
    from_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    to_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    template_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Raw webhook payload for debugging / replay
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Delivery tracking
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="whatsapp_messages")  # type: ignore[name-defined]

    __table_args__ = (
        Index("idx_wa_workspace_contact", "workspace_id", "contact_id"),
        Index("idx_wa_from_number", "workspace_id", "from_number"),
        Index("idx_wa_direction", "workspace_id", "direction"),
    )

    def __repr__(self) -> str:
        return f"<WhatsAppMessage id={self.id} dir={self.direction} status={self.status}>"
