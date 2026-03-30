"""Billing schemas for Razorpay subscriptions and payments."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import Field

from app.models.billing import BillingPlan, PaymentStatus, SubscriptionStatus
from app.schemas.base import FlowraSchema


class CreateSubscriptionRequest(FlowraSchema):
    plan: BillingPlan
    razorpay_plan_id: str = Field(..., description="Razorpay Plan ID (plan_xxxx)")


class SubscriptionResponse(FlowraSchema):
    id: str
    workspace_id: str
    razorpay_subscription_id: Optional[str] = None
    plan: BillingPlan
    status: SubscriptionStatus
    current_start: Optional[datetime] = None
    current_end: Optional[datetime] = None
    next_charge_at: Optional[datetime] = None
    created_at: datetime


class PaymentResponse(FlowraSchema):
    id: str
    workspace_id: str
    subscription_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatus
    invoice_number: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


class RazorpayWebhookPayload(FlowraSchema):
    """Raw Razorpay webhook body (passthrough — we trust signature, parse payload)."""
    event: str
    payload: Dict[str, Any]


# Aliases
SubscriptionOut = SubscriptionResponse
PaymentOut = PaymentResponse
