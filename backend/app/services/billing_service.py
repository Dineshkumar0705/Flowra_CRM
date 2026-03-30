"""
Razorpay subscription billing service.

Handles:
  - Creating a Razorpay subscription on plan upgrade
  - Processing webhook events:
      subscription.activated → mark workspace plan active
      subscription.charged   → record payment, generate invoice
      subscription.halted    → send warning (email/Slack)
      subscription.cancelled → downgrade workspace plan
  - GST invoice generation (placeholder — real PDF via pdf service)
  - Payment history retrieval

Razorpay API docs: https://razorpay.com/docs/api/
"""

import hashlib
import hmac
import json
import logging
import urllib.request
import urllib.parse
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BillingError, IntegrationError
from app.models.billing import (
    BillingPlan,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
)
from app.models.workspace import WorkspacePlan
from app.repositories.workspace_repo import WorkspaceRepository

log = logging.getLogger("flowra.service.billing")

_RZ_BASE = "https://api.razorpay.com/v1"

_PLAN_MAP = {
    BillingPlan.STARTER: WorkspacePlan.STARTER,
    BillingPlan.GROWTH: WorkspacePlan.GROWTH,
    BillingPlan.AGENCY: WorkspacePlan.AGENCY,
}


def _rz_request(method: str, path: str, body: Optional[dict] = None) -> dict:
    """Make an authenticated request to Razorpay."""
    key_id = settings.RAZORPAY_KEY_ID
    key_secret = settings.RAZORPAY_KEY_SECRET
    if not key_id or not key_secret:
        raise IntegrationError("Razorpay", "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET not configured.")

    url = f"{_RZ_BASE}{path}"
    credentials = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body_str = exc.read().decode()
        raise IntegrationError("Razorpay", f"HTTP {exc.code}: {body_str}") from exc


class BillingService:
    """Razorpay subscription billing."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.workspace_repo = WorkspaceRepository(db)

    # ------------------------------------------------------------------
    # Create subscription
    # ------------------------------------------------------------------

    def create_subscription(
        self,
        plan: BillingPlan,
        razorpay_plan_id: str,
        total_count: int = 12,
    ) -> Subscription:
        """
        Create a Razorpay subscription and store it locally.

        Args:
            plan:             The Flowra billing plan.
            razorpay_plan_id: The Razorpay plan_XXXX ID.
            total_count:      Number of billing cycles (default 12 = annual).

        Returns:
            The new Subscription row.
        """
        response = _rz_request("POST", "/subscriptions", {
            "plan_id": razorpay_plan_id,
            "total_count": total_count,
            "quantity": 1,
            "notes": {
                "workspace_id": self.workspace_id,
                "plan": plan,
            },
        })

        subscription = Subscription(
            workspace_id=self.workspace_id,
            razorpay_subscription_id=response.get("id"),
            razorpay_plan_id=razorpay_plan_id,
            plan=plan,
            status=SubscriptionStatus.CREATED,
            raw_payload=response,
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        log.info("billing.subscription_created", subscription_id=subscription.id, plan=plan)
        return subscription

    # ------------------------------------------------------------------
    # Webhook dispatcher
    # ------------------------------------------------------------------

    def handle_webhook(self, payload: Dict[str, Any], raw_body: bytes, signature: str) -> str:
        """
        Validate and dispatch a Razorpay webhook event.

        Args:
            payload:   Parsed JSON body.
            raw_body:  Raw request bytes (for signature verification).
            signature: X-Razorpay-Signature header.

        Returns:
            A human-readable result message.
        """
        self._verify_signature(raw_body, signature)

        event = payload.get("event", "")
        entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})

        log.info("billing.webhook_received", event=event)

        handlers = {
            "subscription.activated": self._on_activated,
            "subscription.charged": self._on_charged,
            "subscription.halted": self._on_halted,
            "subscription.cancelled": self._on_cancelled,
            "subscription.completed": self._on_cancelled,
            "payment.captured": self._on_payment_captured,
        }

        handler = handlers.get(event)
        if handler:
            return handler(entity, payload)

        return f"Event '{event}' acknowledged but not handled."

    # ------------------------------------------------------------------
    # Webhook event handlers
    # ------------------------------------------------------------------

    def _on_activated(self, entity: dict, raw: dict) -> str:
        sub = self._get_subscription_by_rz_id(entity.get("id"))
        if sub:
            sub.status = SubscriptionStatus.ACTIVE
            sub.current_start = self._rz_timestamp(entity.get("current_start"))
            sub.current_end = self._rz_timestamp(entity.get("current_end"))
            sub.raw_payload = entity
            self.db.commit()

            # Upgrade workspace plan
            workspace = self.workspace_repo.get_by_id(self.workspace_id)
            if workspace:
                workspace_plan = _PLAN_MAP.get(sub.plan, WorkspacePlan.STARTER)
                self.workspace_repo.update(workspace, {
                    "plan": workspace_plan,
                    "plan_expires_at": sub.current_end,
                })

            log.info("billing.activated", workspace=self.workspace_id, plan=sub.plan)
        return "subscription.activated processed"

    def _on_charged(self, entity: dict, raw: dict) -> str:
        sub = self._get_subscription_by_rz_id(entity.get("id"))
        payment_entity = raw.get("payload", {}).get("payment", {}).get("entity", {})

        if sub and payment_entity:
            amount_paise = payment_entity.get("amount", 0)
            amount_inr = amount_paise / 100.0

            payment = Payment(
                workspace_id=self.workspace_id,
                subscription_id=sub.id,
                razorpay_payment_id=payment_entity.get("id"),
                razorpay_order_id=payment_entity.get("order_id"),
                amount=amount_inr,
                currency=payment_entity.get("currency", "INR"),
                status=PaymentStatus.CAPTURED,
                paid_at=datetime.now(timezone.utc),
                raw_payload=payment_entity,
            )
            self.db.add(payment)

            # Extend subscription period
            sub.current_end = self._rz_timestamp(entity.get("current_end"))
            sub.next_charge_at = self._rz_timestamp(entity.get("next_charge_at"))
            self.db.commit()
            self.db.refresh(payment)

            # Generate invoice number
            payment.invoice_number = f"INV-{payment.id[:8].upper()}"
            self.db.commit()

            log.info("billing.charged", payment_id=payment.id, amount=amount_inr)
        return "subscription.charged processed"

    def _on_halted(self, entity: dict, raw: dict) -> str:
        sub = self._get_subscription_by_rz_id(entity.get("id"))
        if sub:
            sub.status = SubscriptionStatus.HALTED
            self.db.commit()
            log.warning("billing.halted", workspace=self.workspace_id)
        return "subscription.halted processed"

    def _on_cancelled(self, entity: dict, raw: dict) -> str:
        sub = self._get_subscription_by_rz_id(entity.get("id"))
        if sub:
            sub.status = SubscriptionStatus.CANCELLED
            sub.ended_at = datetime.now(timezone.utc)
            self.db.commit()

            # Downgrade workspace to starter
            workspace = self.workspace_repo.get_by_id(self.workspace_id)
            if workspace:
                self.workspace_repo.update(workspace, {"plan": WorkspacePlan.STARTER})

            log.info("billing.cancelled", workspace=self.workspace_id)
        return "subscription.cancelled processed"

    def _on_payment_captured(self, entity: dict, raw: dict) -> str:
        payment_entity = raw.get("payload", {}).get("payment", {}).get("entity", {})
        if payment_entity:
            existing = (
                self.db.query(Payment)
                .filter(Payment.razorpay_payment_id == payment_entity.get("id"))
                .first()
            )
            if existing:
                existing.status = PaymentStatus.CAPTURED
                self.db.commit()
        return "payment.captured processed"

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_subscription(self) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.workspace_id == self.workspace_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.AUTHENTICATED]),
            )
            .order_by(Subscription.created_at.desc())
            .first()
        )

    def get_payment_history(self, skip: int = 0, limit: int = 20) -> List[Payment]:
        return (
            self.db.query(Payment)
            .filter(Payment.workspace_id == self.workspace_id)
            .order_by(Payment.created_at.desc())
            .offset(skip).limit(limit).all()
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_subscription_by_rz_id(self, rz_id: Optional[str]) -> Optional[Subscription]:
        if not rz_id:
            return None
        return (
            self.db.query(Subscription)
            .filter(Subscription.razorpay_subscription_id == rz_id)
            .first()
        )

    def _verify_signature(self, body: bytes, signature: str) -> None:
        secret = settings.RAZORPAY_WEBHOOK_SECRET or ""
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            raise IntegrationError("Razorpay", "Webhook signature verification failed.")

    @staticmethod
    def _rz_timestamp(ts: Any) -> Optional[datetime]:
        """Convert a Razorpay UNIX timestamp to a UTC datetime."""
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            return None
