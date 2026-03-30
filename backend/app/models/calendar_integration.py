"""Google Calendar integration model."""

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CalendarIntegration(Base, TimestampMixin):
    """
    Stores Google Calendar OAuth2 tokens per user per workspace.
    Tokens are Fernet-encrypted at rest (same pattern as GmailIntegration).
    """

    __tablename__ = "calendar_integrations"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Google account email associated with this integration
    google_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # OAuth2 tokens — Fernet-encrypted JSON blobs
    encrypted_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Primary calendar ID (usually the user's email)
    primary_calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<CalendarIntegration workspace={self.workspace_id} user={self.user_id}>"
