"""
Gmail OAuth2 integration service.

Handles:
  - OAuth2 flow: generate auth URL → exchange code → store encrypted tokens
  - Sync last N emails on first connect
  - Auto-match emails to contacts
  - Send email on behalf of user
  - Email open tracking via pixel
  - Token refresh when expired

Tokens at rest are encrypted with Fernet (OAUTH_ENCRYPTION_KEY env var).
If the key is not set, tokens are stored as plain text (dev mode only).

Gmail API reference: https://developers.google.com/gmail/api
"""

import base64
import json
import logging
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import IntegrationError, NotFoundError
from app.models.gmail_integration import EmailDirection, EmailMessage, GmailIntegration
from app.repositories.contact_repo import ContactRepository

log = logging.getLogger("flowra.service.gmail")

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
]


def _encrypt(text: str) -> str:
    """Encrypt a string using Fernet if the key is configured, else store as-is."""
    key = settings.OAUTH_ENCRYPTION_KEY
    if not key:
        return text  # dev mode — no encryption
    try:
        from cryptography.fernet import Fernet  # type: ignore
        return Fernet(key.encode()).encrypt(text.encode()).decode()
    except ImportError:
        return text  # cryptography not installed


def _decrypt(text: str) -> str:
    """Decrypt a Fernet-encrypted string, or return as-is if not encrypted."""
    key = settings.OAUTH_ENCRYPTION_KEY
    if not key:
        return text
    try:
        from cryptography.fernet import Fernet  # type: ignore
        return Fernet(key.encode()).decrypt(text.encode()).decode()
    except Exception:
        return text


def _google_post(url: str, data: dict) -> dict:
    """Make a POST to a Google API endpoint."""
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read().decode()
        raise IntegrationError("Gmail", f"HTTP {exc.code}: {body}") from exc


def _gmail_get(path: str, access_token: str) -> dict:
    """Make an authenticated GET to the Gmail API."""
    url = f"{_GMAIL_API_BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read().decode()
        raise IntegrationError("Gmail", f"HTTP {exc.code}: {body}") from exc


def _gmail_post(path: str, access_token: str, body: dict) -> dict:
    """Make an authenticated POST to the Gmail API."""
    url = f"{_GMAIL_API_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read().decode()
        raise IntegrationError("Gmail", f"HTTP {exc.code}: {body}") from exc


class GmailService:
    """Gmail OAuth2 integration."""

    def __init__(self, db: Session, workspace_id: str, user_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.contact_repo = ContactRepository(db, workspace_id)

    # ------------------------------------------------------------------
    # OAuth flow
    # ------------------------------------------------------------------

    def get_auth_url(self) -> str:
        """Generate the Google OAuth2 authorization URL."""
        if not settings.GOOGLE_CLIENT_ID:
            raise IntegrationError("Gmail", "GOOGLE_CLIENT_ID is not configured.")

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": f"{self.workspace_id}:{self.user_id}",
        }
        return f"{_GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def handle_oauth_callback(self, code: str) -> GmailIntegration:
        """
        Exchange the auth code for tokens and persist the integration.

        Args:
            code: The OAuth2 authorization code from Google's redirect.

        Returns:
            The new GmailIntegration DB row.
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise IntegrationError("Gmail", "Google OAuth credentials are not configured.")

        # Exchange code for tokens
        token_data = _google_post(_GOOGLE_TOKEN_URL, {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)

        # Get the user's email
        userinfo = _gmail_get("/", access_token)  # placeholder — see note
        # Actually use userinfo endpoint
        try:
            req = urllib.request.Request(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                userinfo = json.loads(resp.read())
            google_email = userinfo.get("email", "")
        except Exception:
            google_email = ""

        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Upsert integration
        existing = self._get_integration()
        if existing:
            existing.access_token_enc = _encrypt(access_token)
            if refresh_token:
                existing.refresh_token_enc = _encrypt(refresh_token)
            existing.token_expiry = expiry
            existing.google_email = google_email
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            integration = existing
        else:
            integration = GmailIntegration(
                workspace_id=self.workspace_id,
                user_id=self.user_id,
                google_email=google_email,
                access_token_enc=_encrypt(access_token),
                refresh_token_enc=_encrypt(refresh_token) if refresh_token else None,
                token_expiry=expiry,
            )
            self.db.add(integration)
            self.db.commit()
            self.db.refresh(integration)

        log.info("gmail.connected", user_id=self.user_id, email=google_email)

        # Kick off initial email sync in the background (fire-and-forget)
        try:
            self.sync_emails(integration, max_results=100)
        except Exception as exc:
            log.warning("gmail.initial_sync_failed", error=str(exc))

        return integration

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _get_integration(self) -> Optional[GmailIntegration]:
        return (
            self.db.query(GmailIntegration)
            .filter(
                GmailIntegration.workspace_id == self.workspace_id,
                GmailIntegration.user_id == self.user_id,
                GmailIntegration.is_active == True,
            )
            .first()
        )

    def _get_valid_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary."""
        integration = self._get_integration()
        if not integration:
            raise IntegrationError("Gmail", "No Gmail account connected.")

        now = datetime.now(timezone.utc)
        token_expiry = integration.token_expiry
        if token_expiry and token_expiry.tzinfo is None:
            token_expiry = token_expiry.replace(tzinfo=timezone.utc)

        if token_expiry and now >= token_expiry - timedelta(minutes=5):
            # Refresh the token
            if not integration.refresh_token_enc:
                raise IntegrationError("Gmail", "No refresh token available. Please reconnect.")

            refresh_token = _decrypt(integration.refresh_token_enc)
            token_data = _google_post(_GOOGLE_TOKEN_URL, {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            })
            new_access = token_data.get("access_token", "")
            new_expiry = now + timedelta(seconds=token_data.get("expires_in", 3600))
            integration.access_token_enc = _encrypt(new_access)
            integration.token_expiry = new_expiry
            self.db.commit()
            return new_access

        return _decrypt(integration.access_token_enc)

    # ------------------------------------------------------------------
    # Email sync
    # ------------------------------------------------------------------

    def sync_emails(self, integration: Optional[GmailIntegration] = None, max_results: int = 50) -> int:
        """
        Pull the latest emails from Gmail and store them in the DB.

        Returns the number of new emails stored.
        """
        if integration is None:
            integration = self._get_integration()
        if not integration:
            raise IntegrationError("Gmail", "No Gmail account connected.")

        access_token = _decrypt(integration.access_token_enc)
        count = 0

        try:
            list_resp = _gmail_get(f"/users/me/messages?maxResults={max_results}", access_token)
            messages = list_resp.get("messages", [])

            for msg_ref in messages:
                msg_id = msg_ref.get("id")
                if not msg_id:
                    continue

                # Skip if already stored
                existing = (
                    self.db.query(EmailMessage)
                    .filter(EmailMessage.gmail_message_id == msg_id)
                    .first()
                )
                if existing:
                    continue

                try:
                    full_msg = _gmail_get(f"/users/me/messages/{msg_id}?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=To&metadataHeaders=Date", access_token)
                    self._store_email(full_msg, integration)
                    count += 1
                except Exception as exc:
                    log.warning("gmail.message_sync_failed", msg_id=msg_id, error=str(exc))
                    continue

        except IntegrationError as exc:
            log.error("gmail.sync_failed", error=str(exc))
            raise

        integration.last_sync_at = datetime.now(timezone.utc)
        integration.synced_messages_count = (integration.synced_messages_count or 0) + count
        self.db.commit()

        log.info("gmail.sync_complete", count=count, user_id=self.user_id)
        return count

    def _store_email(self, msg_data: dict, integration: GmailIntegration) -> EmailMessage:
        """Parse a Gmail message and store it as an EmailMessage row."""
        headers = {h["name"]: h["value"] for h in msg_data.get("payload", {}).get("headers", [])}
        from_email = headers.get("From", "")
        to_email = headers.get("To", "")
        subject = headers.get("Subject")

        # Extract plain email address from "Name <email>" format
        def _extract_email(s: str) -> str:
            if "<" in s and ">" in s:
                return s.split("<")[1].rstrip(">").strip()
            return s.strip()

        from_clean = _extract_email(from_email)
        to_clean = _extract_email(to_email)

        # Determine direction: if from_email matches the integration email → outbound
        direction = (
            EmailDirection.OUTBOUND
            if integration.google_email and from_clean.lower() == integration.google_email.lower()
            else EmailDirection.INBOUND
        )

        # Match to contact
        contact_email = to_clean if direction == EmailDirection.OUTBOUND else from_clean
        contact = self.contact_repo.get_by_email(contact_email)

        email = EmailMessage(
            workspace_id=self.workspace_id,
            contact_id=contact.id if contact else None,
            gmail_integration_id=integration.id,
            gmail_message_id=msg_data.get("id"),
            gmail_thread_id=msg_data.get("threadId"),
            direction=direction,
            from_email=from_clean,
            to_email=to_clean,
            subject=subject,
            body_text=None,  # full sync omitted for performance; fetch on demand
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(email)
        self.db.commit()

        if contact:
            contact.last_contacted_at = datetime.now(timezone.utc)
            self.db.commit()

        return email

    # ------------------------------------------------------------------
    # Send email
    # ------------------------------------------------------------------

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        contact_id: Optional[str] = None,
    ) -> EmailMessage:
        """
        Send an email via the connected Gmail account.

        A 1×1 tracking pixel is embedded in the body to record opens.
        """
        access_token = self._get_valid_access_token()
        integration = self._get_integration()
        if not integration:
            raise IntegrationError("Gmail", "No Gmail account connected.")

        # Generate tracking pixel
        tracking_id = str(uuid.uuid4())
        base_url = settings.GOOGLE_REDIRECT_URI.split("/api")[0]
        pixel_url = f"{base_url}/api/v1/gmail/track/{tracking_id}"
        body_with_pixel = f"{body_html}<img src='{pixel_url}' width='1' height='1' style='display:none;' />"

        # Build MIME message
        msg = MIMEMultipart("alternative")
        msg["to"] = to_email
        msg["from"] = integration.google_email
        msg["subject"] = subject
        msg.attach(MIMEText(body_with_pixel, "html"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        _gmail_post("/users/me/messages/send", access_token, {"raw": raw})

        # Store in DB
        email = EmailMessage(
            workspace_id=self.workspace_id,
            contact_id=contact_id,
            gmail_integration_id=integration.id,
            direction=EmailDirection.OUTBOUND,
            from_email=integration.google_email,
            to_email=to_email,
            subject=subject,
            tracking_pixel_id=tracking_id,
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)

        log.info("gmail.sent", to=to_email, message_id=email.id)
        return email

    # ------------------------------------------------------------------
    # Open tracking
    # ------------------------------------------------------------------

    def record_email_open(self, tracking_id: str) -> None:
        """Record a tracking pixel hit — i.e., the email was opened."""
        email = (
            self.db.query(EmailMessage)
            .filter(EmailMessage.tracking_pixel_id == tracking_id)
            .first()
        )
        if not email:
            return
        email.open_count = (email.open_count or 0) + 1
        if not email.first_opened_at:
            email.first_opened_at = datetime.now(timezone.utc)
        self.db.commit()
        log.info("gmail.open_tracked", tracking_id=tracking_id)
