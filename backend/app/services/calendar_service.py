"""
Google Calendar integration service.

Handles:
  - OAuth2 connect/callback flow (reuses same Google Cloud project as Gmail)
  - Creating calendar events (kickoff calls, follow-ups)
  - Listing upcoming events
  - Token encryption/refresh (mirrors GmailService pattern)

Prerequisites (same Google Cloud app as Gmail):
  - Enable Google Calendar API in Google Cloud Console
  - Add calendar scopes to OAuth consent screen:
      https://www.googleapis.com/auth/calendar.events
  - Set GOOGLE_CALENDAR_REDIRECT_URI in .env
"""

import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import IntegrationError, NotFoundError
from app.models.calendar_integration import CalendarIntegration

log = logging.getLogger("flowra.service.calendar")

# Google OAuth2 + Calendar API endpoints
_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

# Scopes requested
_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
    "openid",
    "email",
]


def _fernet():
    """Return a Fernet instance for token encryption."""
    from cryptography.fernet import Fernet
    key = settings.OAUTH_ENCRYPTION_KEY
    if not key:
        # In dev without a key, use a deterministic key derived from SECRET_KEY
        import base64
        import hashlib
        derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(derived).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def _decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


def _google_api_call(
    url: str,
    access_token: str,
    method: str = "GET",
    body: Optional[dict] = None,
) -> dict:
    """Make an authenticated Google API call via stdlib urllib."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode(errors="replace")
        raise IntegrationError(
            f"Google Calendar API error {exc.code}: {error_body}",
            service="google_calendar",
        )


class CalendarService:
    """Google Calendar integration — connect, create events, list events."""

    def __init__(self, db: Session, workspace_id: str, user_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.user_id = user_id

    # ------------------------------------------------------------------
    # OAuth2 flow
    # ------------------------------------------------------------------

    def get_auth_url(self) -> str:
        """
        Return the Google OAuth2 URL to redirect the user to.
        State encodes workspace_id:user_id for callback routing.
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise IntegrationError(
                "Google OAuth is not configured. Set GOOGLE_CLIENT_ID in .env.",
                service="google_calendar",
            )

        state = f"{self.workspace_id}:{self.user_id}"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(_SCOPES),
            "access_type": "offline",
            "prompt": "consent",   # always get refresh_token
            "state": state,
        }
        return f"{_OAUTH_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def handle_oauth_callback(self, code: str) -> CalendarIntegration:
        """
        Exchange the authorization code for tokens and store them.
        Creates a new CalendarIntegration row (or updates existing).
        """
        # Exchange code for tokens
        body = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_CALENDAR_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        data = urllib.parse.urlencode(body).encode()
        req = urllib.request.Request(_OAUTH_TOKEN_URL, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise IntegrationError(
                f"Google token exchange failed: {exc.read().decode()}",
                service="google_calendar",
            )

        access_token = tokens["access_token"]
        refresh_token = tokens.get("refresh_token", "")
        expires_in = tokens.get("expires_in", 3600)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Get user email from Google
        google_email = self._get_google_email(access_token)

        # Get primary calendar ID
        try:
            cal_info = _google_api_call(
                f"{_CALENDAR_API_BASE}/users/me/calendarList/primary", access_token
            )
            primary_calendar_id = cal_info.get("id", google_email)
        except Exception:
            primary_calendar_id = google_email

        # Upsert integration row
        integration = self._get_integration()
        if integration:
            integration.encrypted_access_token = _encrypt(access_token)
            if refresh_token:
                integration.encrypted_refresh_token = _encrypt(refresh_token)
            integration.token_expiry = expiry
            integration.google_email = google_email
            integration.primary_calendar_id = primary_calendar_id
            integration.is_active = True
        else:
            integration = CalendarIntegration(
                workspace_id=self.workspace_id,
                user_id=self.user_id,
                google_email=google_email,
                encrypted_access_token=_encrypt(access_token),
                encrypted_refresh_token=_encrypt(refresh_token) if refresh_token else None,
                token_expiry=expiry,
                primary_calendar_id=primary_calendar_id,
                is_active=True,
            )
            self.db.add(integration)

        self.db.commit()
        self.db.refresh(integration)
        log.info("calendar.connected", workspace_id=self.workspace_id, email=google_email)
        return integration

    # ------------------------------------------------------------------
    # Event management
    # ------------------------------------------------------------------

    def create_event(
        self,
        summary: str,
        description: str = "",
        start_datetime: Optional[datetime] = None,
        duration_minutes: int = 60,
        attendee_emails: Optional[List[str]] = None,
        location: str = "",
        meet_link: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a Google Calendar event.

        Returns the created event dict including:
          - id: event ID
          - htmlLink: URL to open in browser
          - hangoutLink: Google Meet link (if meet_link=True)
          - start/end: ISO datetime strings
        """
        access_token = self._get_valid_access_token()

        if start_datetime is None:
            # Default: next business day at 10:00 AM IST
            start_datetime = self._next_business_day_10am()

        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        event_body: Dict[str, Any] = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        if attendee_emails:
            event_body["attendees"] = [{"email": e} for e in attendee_emails]

        if meet_link:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"flowra-{self.workspace_id[:8]}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            }

        integration = self._get_integration()
        calendar_id = integration.primary_calendar_id if integration else "primary"

        url = f"{_CALENDAR_API_BASE}/calendars/{urllib.parse.quote(calendar_id)}/events"
        if meet_link:
            url += "?conferenceDataVersion=1"

        result = _google_api_call(url, access_token, method="POST", body=event_body)
        log.info(
            "calendar.event_created",
            workspace_id=self.workspace_id,
            event_id=result.get("id"),
            summary=summary,
        )
        return result

    def create_kickoff_event(
        self,
        client_name: str,
        client_email: str,
        project_name: str,
        owner_email: str,
        start_datetime: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Create a standard onboarding kickoff call event.
        Called by the OnboardingAutopilot (step 5).
        """
        return self.create_event(
            summary=f"Kickoff Call — {client_name} × {project_name}",
            description=(
                f"Welcome to Flowra!\n\n"
                f"This is your project kickoff call with {client_name}.\n\n"
                f"Agenda:\n"
                f"1. Project goals and timeline\n"
                f"2. Communication preferences\n"
                f"3. Next milestones\n\n"
                f"Project: {project_name}"
            ),
            start_datetime=start_datetime,
            duration_minutes=60,
            attendee_emails=[client_email, owner_email],
            meet_link=True,
        )

    def list_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 10,
    ) -> List[Dict[str, Any]]:
        """List upcoming calendar events."""
        access_token = self._get_valid_access_token()
        integration = self._get_integration()
        calendar_id = integration.primary_calendar_id if integration else "primary"

        if time_min is None:
            time_min = datetime.now(timezone.utc)
        if time_max is None:
            time_max = time_min + timedelta(days=30)

        params = urllib.parse.urlencode({
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "maxResults": max_results,
            "singleEvents": "true",
            "orderBy": "startTime",
        })
        url = f"{_CALENDAR_API_BASE}/calendars/{urllib.parse.quote(calendar_id)}/events?{params}"
        result = _google_api_call(url, access_token)
        return result.get("items", [])

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _get_integration(self) -> Optional[CalendarIntegration]:
        return self.db.query(CalendarIntegration).filter(
            CalendarIntegration.workspace_id == self.workspace_id,
            CalendarIntegration.user_id == self.user_id,
            CalendarIntegration.is_active == True,  # noqa: E712
        ).first()

    def _get_valid_access_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        integration = self._get_integration()
        if not integration:
            raise IntegrationError(
                "Google Calendar is not connected. Call GET /calendar/connect first.",
                service="google_calendar",
            )

        now = datetime.now(timezone.utc)
        buffer = timedelta(minutes=5)

        if integration.token_expiry and integration.token_expiry - buffer > now:
            # Token still valid
            return _decrypt(integration.encrypted_access_token)

        # Refresh
        if not integration.encrypted_refresh_token:
            raise IntegrationError(
                "Google Calendar refresh token missing. Reconnect via /calendar/connect.",
                service="google_calendar",
            )

        refresh_token = _decrypt(integration.encrypted_refresh_token)
        body = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        data = urllib.parse.urlencode(body).encode()
        req = urllib.request.Request(_OAUTH_TOKEN_URL, data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            raise IntegrationError(
                f"Google token refresh failed: {exc.read().decode()}",
                service="google_calendar",
            )

        access_token = tokens["access_token"]
        expires_in = tokens.get("expires_in", 3600)

        integration.encrypted_access_token = _encrypt(access_token)
        integration.token_expiry = now + timedelta(seconds=expires_in)
        self.db.commit()

        return access_token

    def _get_google_email(self, access_token: str) -> str:
        """Fetch the Google account email from the userinfo endpoint."""
        try:
            result = _google_api_call(
                "https://www.googleapis.com/oauth2/v3/userinfo", access_token
            )
            return result.get("email", "")
        except Exception:
            return ""

    @staticmethod
    def _next_business_day_10am() -> datetime:
        """Return next Monday–Friday at 10:00 AM IST from now."""
        from zoneinfo import ZoneInfo
        ist = ZoneInfo("Asia/Kolkata")
        now = datetime.now(ist)
        candidate = now + timedelta(days=1)
        # Skip weekends
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        return candidate.replace(hour=10, minute=0, second=0, microsecond=0)
