"""
Billing models: Subscription and Payment.

Razorpay is the payment processor (India-native, UPI support).
Subscriptions are linked to Workspaces.
Payments record individual charge events for audit / invoice generation.
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SubscriptionStatus(str, enum.Enum):
    CREATED = "created"
    AUTHENTICATED = "authenticated"
    ACTIVE = "active"
    HALTED = "halted"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


class BillingPlan(str, enum.Enum):
    STARTER = "starter"
    GROWTH = "growth"
    AGENCY = "agency"


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------

class Subscription(TimestampMixin, Base):
    """
    A Razorpay subscription tied to a Workspace.

    Lifecycle:
      created → authenticated → active → (halted | cancelled | expired)

    Webhook handlers in billing_service.py drive the status transitions.
    """

    __tablename__ = "subscriptions"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    razorpay_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    razorpay_plan_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    plan: Mapped[BillingPlan] = mapped_column(
        Enum(BillingPlan), nullable=False, index=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.CREATED, nullable=False, index=True
    )

    current_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_charge_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    charge_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Store the full Razorpay subscription object for debugging
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    payments: Mapped[list["Payment"]] = relationship(
        "Payment", back_populates="subscription", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_subscription_workspace", "workspace_id"),
        Index("idx_subscription_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} plan={self.plan} status={self.status}>"

    @property
    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class Payment(TimestampMixin, Base):
    """
    An individual charge / payment event.

    Created when Razorpay fires a subscription.charged webhook.
    Used to generate GST invoices and for reconciliation.
    """

    __tablename__ = "payments"

    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)   # in INR
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True
    )

    # GST
    gst_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    invoice_pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)

    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    subscription: Mapped[Optional[Subscription]] = relationship("Subscription", back_populates="payments")

    __table_args__ = (
        Index("idx_payment_workspace", "workspace_id"),
        Index("idx_payment_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Payment id={self.id} amount={self.amount} status={self.status}>"
