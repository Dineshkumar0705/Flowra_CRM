"""
Gmail integration models.

GmailIntegration stores the encrypted OAuth2 tokens for a user's connected
Gmail account.  EmailMessage stores the synced email threads / messages.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# GmailIntegration — OAuth token storage
# ---------------------------------------------------------------------------

class GmailIntegration(TimestampMixin, Base):
    """
    OAuth2 credentials for a user's connected Gmail account.

    Tokens are stored encrypted using Fernet (OAUTH_ENCRYPTION_KEY env var).
    One user can have at most one Gmail integration per workspace.
    """

    __tablename__ = "gmail_integrations"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    google_email: Mapped[str] = mapped_column(String(255), nullable=False)

    # Tokens stored as Fernet-encrypted strings
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    synced_messages_count: Mapped[int] = mapped_column(default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_gmail_per_user_workspace"),
        Index("idx_gmail_workspace", "workspace_id"),
    )

    def __repr__(self) -> str:
        return f"<GmailIntegration user={self.user_id} email={self.google_email}>"


# ---------------------------------------------------------------------------
# EmailMessage
# ---------------------------------------------------------------------------

class EmailDirection(str, enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class EmailMessage(TimestampMixin, Base):
    """
    A synced email message from / to a contact.

    Body content is stored as plain text (HTML is stripped on sync).
    We embed a 1×1 tracking pixel in outbound HTML bodies and record
    the first open in first_opened_at.
    """

    __tablename__ = "email_messages"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    gmail_integration_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("gmail_integrations.id", ondelete="SET NULL"),
        nullable=True,
    )

    gmail_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True, index=True)
    gmail_thread_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)

    direction: Mapped[EmailDirection] = mapped_column(
        Enum(EmailDirection), nullable=False, index=True
    )

    from_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Email open tracking
    tracking_pixel_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, unique=True)
    first_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(default=0, nullable=False)

    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="email_messages")  # type: ignore[name-defined]

    __table_args__ = (
        Index("idx_email_workspace_contact", "workspace_id", "contact_id"),
        Index("idx_email_thread", "gmail_thread_id"),
    )

    def __repr__(self) -> str:
        return f"<EmailMessage id={self.id} dir={self.direction} subject='{self.subject}'>"
