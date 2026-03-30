"""
Contact model — the people in your CRM.

Contacts are workspace-scoped.  A contact may be linked to multiple deals.
WhatsApp messages and Gmail threads are linked via phone / email FK lookups.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin


class ContactSource(str, enum.Enum):
    MANUAL = "manual"
    IMPORT = "import"
    WHATSAPP = "whatsapp"
    GMAIL = "gmail"
    WEB_FORM = "web_form"
    REFERRAL = "referral"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class Contact(TimestampMixin, SoftDeleteMixin, Base):
    """
    A person in the CRM.

    Design decisions:
    - email is unique per workspace (enforced by UniqueConstraint)
    - lead_score is AI-calculated (0–100)
    - tags / custom_fields use JSONB for flexibility
    - last_contacted_at is updated by WhatsApp / Gmail sync jobs
    """

    __tablename__ = "contacts"

    # ------------------------------------------------------------------
    # Multi-tenancy — EVERY query must filter on workspace_id
    # ------------------------------------------------------------------
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    whatsapp_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ------------------------------------------------------------------
    # Professional
    # ------------------------------------------------------------------
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ------------------------------------------------------------------
    # Lead scoring & metadata
    # ------------------------------------------------------------------
    source: Mapped[ContactSource] = mapped_column(
        Enum(ContactSource), default=ContactSource.MANUAL, nullable=False, index=True
    )
    lead_status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, nullable=False, index=True
    )
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # ------------------------------------------------------------------
    # Activity tracking
    # ------------------------------------------------------------------
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="contacts")  # type: ignore[name-defined]
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])  # type: ignore[name-defined]
    deals: Mapped[list["Deal"]] = relationship("Deal", back_populates="contact")  # type: ignore[name-defined]
    whatsapp_messages: Mapped[list["WhatsAppMessage"]] = relationship("WhatsAppMessage", back_populates="contact", cascade="all, delete-orphan")  # type: ignore[name-defined]
    email_messages: Mapped[list["EmailMessage"]] = relationship("EmailMessage", back_populates="contact", cascade="all, delete-orphan")  # type: ignore[name-defined]

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    __table_args__ = (
        UniqueConstraint("workspace_id", "email", name="uq_contact_email_per_workspace"),
        Index("idx_contact_workspace", "workspace_id"),
        Index("idx_contact_company", "workspace_id", "company_name"),
        Index("idx_contact_lead_score", "workspace_id", "lead_score"),
    )

    def __repr__(self) -> str:
        return f"<Contact id={self.id} name={self.first_name} {self.last_name}>"

    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.last_name:
            parts.append(self.last_name)
        return " ".join(parts)
