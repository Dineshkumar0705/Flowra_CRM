"""Gmail routes — OAuth flow, email sync, send, open tracking."""

from fastapi import APIRouter, Query, Request, status
from fastapi.responses import Response

from app.api.deps import CurrentUserDep, DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.schemas.gmail import EmailMessageOut, GmailIntegrationOut, SendEmailRequest
from app.services.gmail_service import GmailService

router = APIRouter()


# ---------------------------------------------------------------------------
# OAuth flow
# ---------------------------------------------------------------------------


@router.get("/connect", response_model=SuccessResponse[dict])
def get_gmail_auth_url(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the Google OAuth2 authorization URL to connect Gmail."""
    svc = GmailService(db, workspace_id, current_user.id)
    url = svc.get_auth_url()
    return success({"auth_url": url})


@router.get("/callback", response_model=SuccessResponse[GmailIntegrationOut])
def gmail_oauth_callback(
    code: str,
    state: str,
    db: DbDep,
):
    """
    Google OAuth2 callback — exchange code for tokens and connect Gmail.
    State format: workspace_id:user_id
    """
    try:
        workspace_id, user_id = state.split(":", 1)
    except ValueError:
        from app.core.exceptions import ValidationError
        raise ValidationError("Invalid OAuth state parameter.")

    svc = GmailService(db, workspace_id, user_id)
    integration = svc.handle_oauth_callback(code)
    return success(GmailIntegrationOut.model_validate(integration), message="Gmail connected successfully.")


@router.get("/status", response_model=SuccessResponse[GmailIntegrationOut])
def gmail_status(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the current Gmail integration status for the user."""
    from app.core.exceptions import NotFoundError
    svc = GmailService(db, workspace_id, current_user.id)
    integration = svc._get_integration()
    if not integration:
        raise NotFoundError("GmailIntegration", "not connected")
    return success(GmailIntegrationOut.model_validate(integration))


# ---------------------------------------------------------------------------
# Email sync and list
# ---------------------------------------------------------------------------


@router.post("/sync", response_model=SuccessResponse[dict])
def sync_emails(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    max_results: int = Query(50, ge=1, le=500),
):
    """Pull the latest emails from Gmail into the CRM."""
    svc = GmailService(db, workspace_id, current_user.id)
    count = svc.sync_emails(max_results=max_results)
    return success({"synced": count}, message=f"{count} new email(s) synced.")


@router.get("/messages", response_model=SuccessResponse[list])
def list_emails(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    contact_id: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List synced email messages, optionally filtered by contact."""
    from app.models.gmail_integration import EmailMessage, GmailIntegration

    skip = (page - 1) * limit
    q = db.query(EmailMessage).filter(
        EmailMessage.workspace_id == workspace_id,
    )
    if contact_id:
        q = q.filter(EmailMessage.contact_id == contact_id)
    items = q.order_by(EmailMessage.sent_at.desc()).offset(skip).limit(limit).all()
    return success([EmailMessageOut.model_validate(e) for e in items])


# ---------------------------------------------------------------------------
# Send email
# ---------------------------------------------------------------------------


@router.post("/send", response_model=SuccessResponse[EmailMessageOut], status_code=status.HTTP_201_CREATED)
def send_email(
    payload: SendEmailRequest,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Send an email via the connected Gmail account."""
    svc = GmailService(db, workspace_id, current_user.id)
    msg = svc.send_email(
        to_email=payload.to_email,
        subject=payload.subject,
        body_html=payload.body_html,
        contact_id=payload.contact_id,
    )
    return success(EmailMessageOut.model_validate(msg), message="Email sent.")


# ---------------------------------------------------------------------------
# Open tracking pixel
# ---------------------------------------------------------------------------


@router.get("/track/{tracking_id}", include_in_schema=False)
def track_email_open(tracking_id: str, db: DbDep):
    """
    1×1 tracking pixel endpoint.
    Called when recipient's email client loads images.
    Returns a transparent GIF and records the open event.
    """
    # Record the open (workspace_id is not needed — tracking_id is globally unique)
    from app.models.gmail_integration import EmailMessage

    email = db.query(EmailMessage).filter(
        EmailMessage.tracking_pixel_id == tracking_id
    ).first()
    if email:
        from datetime import datetime, timezone
        email.open_count = (email.open_count or 0) + 1
        if not email.first_opened_at:
            email.first_opened_at = datetime.now(timezone.utc)
        db.commit()

    # 1×1 transparent GIF
    pixel = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
        b"!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
        b"\x00\x00\x02\x02D\x01\x00;"
    )
    return Response(content=pixel, media_type="image/gif")
