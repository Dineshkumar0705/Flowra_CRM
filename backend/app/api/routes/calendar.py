"""Google Calendar routes — OAuth connect, event creation, event list."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query, status
from pydantic import Field

from app.api.deps import CurrentUserDep, DbDep, WorkspaceIdDep, WorkspaceMemberDep
from app.schemas.base import SuccessResponse, success
from app.core.exceptions import ValidationError
from app.services.calendar_service import CalendarService
from app.schemas.base import FlowraSchema

router = APIRouter()


# ---------------------------------------------------------------------------
# Inline schemas (small enough to not need a separate file)
# ---------------------------------------------------------------------------


class CalendarIntegrationOut(FlowraSchema):
    id: str
    workspace_id: str
    user_id: str
    google_email: Optional[str] = None
    primary_calendar_id: Optional[str] = None
    is_active: bool
    created_at: datetime


class CreateEventRequest(FlowraSchema):
    summary: str = Field(..., min_length=1, max_length=500)
    description: str = ""
    start_datetime: Optional[datetime] = None
    duration_minutes: int = Field(60, ge=15, le=480)
    attendee_emails: List[str] = Field(default_factory=list)
    location: str = ""
    add_meet_link: bool = True


class KickoffEventRequest(FlowraSchema):
    client_name: str = Field(..., min_length=1)
    client_email: str
    project_name: str = Field(..., min_length=1)
    owner_email: str
    start_datetime: Optional[datetime] = None


# ---------------------------------------------------------------------------
# OAuth
# ---------------------------------------------------------------------------


@router.get("/connect", response_model=SuccessResponse[dict])
def get_calendar_auth_url(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Return the Google OAuth2 URL to connect Google Calendar."""
    svc = CalendarService(db, workspace_id, current_user.id)
    url = svc.get_auth_url()
    return success({"auth_url": url})


@router.get("/callback", response_model=SuccessResponse[CalendarIntegrationOut])
def calendar_oauth_callback(
    code: str,
    state: str,
    db: DbDep,
):
    """
    Google OAuth2 callback — exchange code for tokens.
    State format: workspace_id:user_id
    """
    try:
        workspace_id, user_id = state.split(":", 1)
    except ValueError:
        raise ValidationError("Invalid OAuth state parameter.")

    svc = CalendarService(db, workspace_id, user_id)
    integration = svc.handle_oauth_callback(code)
    return success(
        CalendarIntegrationOut.model_validate(integration),
        message="Google Calendar connected successfully.",
    )


@router.get("/status", response_model=SuccessResponse[CalendarIntegrationOut])
def calendar_status(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Check if Google Calendar is connected."""
    from app.core.exceptions import NotFoundError
    svc = CalendarService(db, workspace_id, current_user.id)
    integration = svc._get_integration()
    if not integration:
        raise NotFoundError("CalendarIntegration", "not connected")
    return success(CalendarIntegrationOut.model_validate(integration))


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@router.post("/events", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
def create_event(
    payload: CreateEventRequest,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Create a Google Calendar event from the CRM."""
    svc = CalendarService(db, workspace_id, current_user.id)
    event = svc.create_event(
        summary=payload.summary,
        description=payload.description,
        start_datetime=payload.start_datetime,
        duration_minutes=payload.duration_minutes,
        attendee_emails=payload.attendee_emails,
        location=payload.location,
        meet_link=payload.add_meet_link,
    )
    return success(
        {
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
            "meet_link": event.get("hangoutLink"),
            "start": event.get("start", {}).get("dateTime"),
            "end": event.get("end", {}).get("dateTime"),
        },
        message="Calendar event created.",
    )


@router.post("/events/kickoff", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
def create_kickoff_event(
    payload: KickoffEventRequest,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Create a standard kickoff call event for a new client."""
    svc = CalendarService(db, workspace_id, current_user.id)
    event = svc.create_kickoff_event(
        client_name=payload.client_name,
        client_email=payload.client_email,
        project_name=payload.project_name,
        owner_email=payload.owner_email,
        start_datetime=payload.start_datetime,
    )
    return success(
        {
            "event_id": event.get("id"),
            "html_link": event.get("htmlLink"),
            "meet_link": event.get("hangoutLink"),
            "start": event.get("start", {}).get("dateTime"),
        },
        message="Kickoff call scheduled.",
    )


@router.get("/events", response_model=SuccessResponse[list])
def list_events(
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    max_results: int = Query(10, ge=1, le=100),
):
    """List upcoming Google Calendar events."""
    svc = CalendarService(db, workspace_id, current_user.id)
    events = svc.list_events(max_results=max_results)
    simplified = [
        {
            "event_id": e.get("id"),
            "summary": e.get("summary", ""),
            "start": e.get("start", {}).get("dateTime") or e.get("start", {}).get("date"),
            "end": e.get("end", {}).get("dateTime") or e.get("end", {}).get("date"),
            "html_link": e.get("htmlLink"),
            "meet_link": e.get("hangoutLink"),
            "attendees": [a["email"] for a in e.get("attendees", [])],
        }
        for e in events
    ]
    return success(simplified)
