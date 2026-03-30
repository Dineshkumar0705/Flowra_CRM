"""WhatsApp routes — send messages and handle Meta webhook."""

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import PlainTextResponse

from app.api.deps import DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.schemas.whatsapp import SendTemplateRequest, SendTextRequest, WhatsAppMessageOut
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------


@router.post("/send/text", response_model=SuccessResponse[WhatsAppMessageOut], status_code=status.HTTP_201_CREATED)
def send_text(
    payload: SendTextRequest,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Send a plain text WhatsApp message to a phone number."""
    svc = WhatsAppService(db, workspace_id)
    msg = svc.send_text(payload.to_number, payload.body, contact_id=payload.contact_id)
    return success(WhatsAppMessageOut.model_validate(msg), message="Message sent.")


@router.post("/send/template", response_model=SuccessResponse[WhatsAppMessageOut], status_code=status.HTTP_201_CREATED)
def send_template(
    payload: SendTemplateRequest,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Send a WhatsApp template message."""
    svc = WhatsAppService(db, workspace_id)
    msg = svc.send_template(
        payload.to_number,
        payload.template_name,
        payload.language_code,
        payload.components,
        contact_id=payload.contact_id,
    )
    return success(WhatsAppMessageOut.model_validate(msg), message="Template sent.")


# ---------------------------------------------------------------------------
# Webhook (Meta verification + incoming messages)
# ---------------------------------------------------------------------------


@router.get("/webhook", response_class=PlainTextResponse, include_in_schema=False)
def whatsapp_webhook_verify(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """
    Meta webhook verification handshake.
    Meta sends GET with hub.mode=subscribe to verify ownership.
    """
    from app.core.config import settings
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return hub_challenge
    return PlainTextResponse("Forbidden", status_code=403)


@router.post("/webhook", status_code=status.HTTP_200_OK, include_in_schema=False)
async def whatsapp_webhook_receive(request: Request, db: DbDep):
    """
    Receive incoming WhatsApp messages and delivery status updates.
    Meta requires a 200 response within 20s.
    """
    import json
    from app.core.config import settings

    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Each workspace using WhatsApp would have a token; here we use the global one.
    # In multi-workspace setups, route by phone number ID in the payload.
    payload = json.loads(raw_body)

    # Find workspace by phone number (simplified: use first active WhatsApp workspace)
    # In production, map phone_number_id → workspace_id in DB
    workspace_id = payload.get("entry", [{}])[0].get("id", "")

    svc = WhatsAppService(db, workspace_id or "")
    svc.handle_webhook(payload, raw_body, signature)
    return {"status": "ok"}
