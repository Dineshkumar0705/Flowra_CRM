"""Billing routes — subscription management, Razorpay webhook, payment history."""

from typing import List

from fastapi import APIRouter, Header, Request, status

from app.api.deps import AdminDep, DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.schemas.billing import PaymentOut, SubscriptionOut, CreateSubscriptionRequest
from app.services.billing_service import BillingService

router = APIRouter()


@router.get("/subscription", response_model=SuccessResponse[SubscriptionOut])
def get_subscription(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the current active subscription for the workspace."""
    from app.core.exceptions import NotFoundError
    svc = BillingService(db, workspace_id)
    sub = svc.get_subscription()
    if not sub:
        raise NotFoundError("Subscription", "no active subscription")
    return success(SubscriptionOut.model_validate(sub))


@router.post("/subscription", response_model=SuccessResponse[SubscriptionOut], status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: CreateSubscriptionRequest,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _admin: AdminDep,
):
    """Create a new Razorpay subscription for the workspace. Requires admin/owner."""
    svc = BillingService(db, workspace_id)
    sub = svc.create_subscription(
        plan=payload.plan,
        razorpay_plan_id=payload.razorpay_plan_id,
        total_count=payload.total_count,
    )
    return success(SubscriptionOut.model_validate(sub), message="Subscription created.")


@router.get("/payments", response_model=SuccessResponse[List[PaymentOut]])
def get_payment_history(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    page: int = 1,
    limit: int = 20,
):
    """Return payment history for the workspace."""
    svc = BillingService(db, workspace_id)
    payments = svc.get_payment_history(skip=(page - 1) * limit, limit=limit)
    return success([PaymentOut.model_validate(p) for p in payments])


# ---------------------------------------------------------------------------
# Razorpay webhook (unauthenticated — signature-verified)
# ---------------------------------------------------------------------------


@router.post("/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def razorpay_webhook(
    request: Request,
    db: DbDep,
    x_razorpay_signature: str = Header(default=""),
):
    """
    Razorpay webhook endpoint.
    Events: subscription.activated, subscription.charged, subscription.halted,
            subscription.cancelled, payment.captured
    """
    import json

    raw_body = await request.body()
    payload = json.loads(raw_body)

    # Extract workspace_id from subscription notes
    entity = payload.get("payload", {}).get("subscription", {}).get("entity", {})
    notes = entity.get("notes", {})
    workspace_id = notes.get("workspace_id", "")

    if not workspace_id:
        return {"status": "no workspace found"}

    svc = BillingService(db, workspace_id)
    result = svc.handle_webhook(payload, raw_body, x_razorpay_signature)
    return {"status": "ok", "result": result}
