"""
WhatsApp Business Cloud API service.

Handles:
  - Sending text and template messages via Meta's Graph API
  - Receiving and parsing inbound webhook payloads
  - Linking messages to Contacts by phone number
  - Storing all messages in the whatsapp_messages table

API reference: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

import hashlib
import hmac
import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.models.whatsapp_message import (
    MessageDirection,
    MessageStatus,
    MessageType,
    WhatsAppMessage,
)
from app.repositories.contact_repo import ContactRepository

log = logging.getLogger("flowra.service.whatsapp")

_WA_BASE = "https://graph.facebook.com"


def _wa_request(method: str, path: str, body: Optional[dict] = None) -> dict:
    """
    Make a signed request to the WhatsApp Cloud API.

    Uses stdlib urllib (no httpx / requests needed) so it works without
    additional dependencies.
    """
    token = settings.WHATSAPP_ACCESS_TOKEN
    if not token:
        raise IntegrationError("WhatsApp", "WHATSAPP_ACCESS_TOKEN is not configured.")

    url = f"{_WA_BASE}/{settings.WHATSAPP_API_VERSION}/{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        error_body = exc.read().decode()
        raise IntegrationError("WhatsApp", f"HTTP {exc.code}: {error_body}") from exc
    except URLError as exc:
        raise IntegrationError("WhatsApp", f"Network error: {exc.reason}") from exc


class WhatsAppService:
    """WhatsApp Cloud API integration."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id
        self.contact_repo = ContactRepository(db, workspace_id)

    # ------------------------------------------------------------------
    # Outbound — send messages
    # ------------------------------------------------------------------

    def send_text(
        self,
        to_number: str,
        body: str,
        contact_id: Optional[str] = None,
    ) -> WhatsAppMessage:
        """
        Send a free-form text message.

        Args:
            to_number: E.164 phone number of the recipient.
            body:      Message text (max 4096 chars).
            contact_id: Optional CRM contact to link this message to.

        Returns:
            Persisted WhatsAppMessage row.
        """
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        if not phone_id:
            raise IntegrationError("WhatsApp", "WHATSAPP_PHONE_NUMBER_ID is not configured.")

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }

        wa_msg_id: Optional[str] = None
        try:
            response = _wa_request("POST", f"{phone_id}/messages", payload)
            wa_msg_id = response.get("messages", [{}])[0].get("id")
        except IntegrationError:
            log.warning("whatsapp.send_failed", to=to_number)
            raise

        message = self._persist_outbound(
            to_number=to_number,
            body=body,
            message_type=MessageType.TEXT,
            wa_message_id=wa_msg_id,
            contact_id=contact_id,
        )
        log.info("whatsapp.sent", to=to_number, message_id=message.id)
        return message

    def send_template(
        self,
        to_number: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[list] = None,
        contact_id: Optional[str] = None,
    ) -> WhatsAppMessage:
        """Send a pre-approved template message."""
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        if not phone_id:
            raise IntegrationError("WhatsApp", "WHATSAPP_PHONE_NUMBER_ID is not configured.")

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }

        wa_msg_id: Optional[str] = None
        try:
            response = _wa_request("POST", f"{phone_id}/messages", payload)
            wa_msg_id = response.get("messages", [{}])[0].get("id")
        except IntegrationError:
            log.warning("whatsapp.template_send_failed", to=to_number, template=template_name)
            raise

        return self._persist_outbound(
            to_number=to_number,
            body=None,
            message_type=MessageType.TEMPLATE,
            wa_message_id=wa_msg_id,
            template_name=template_name,
            contact_id=contact_id,
        )

    # ------------------------------------------------------------------
    # Inbound — webhook handler
    # ------------------------------------------------------------------

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Handle the GET verification request from Meta.

        Returns the challenge string if verification passes, None otherwise.
        """
        expected = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
        if mode == "subscribe" and token == expected:
            return challenge
        return None

    def handle_webhook(self, payload: Dict[str, Any], raw_signature: Optional[str] = None) -> int:
        """
        Process an inbound webhook event from Meta.

        Args:
            payload:       Parsed JSON body.
            raw_signature: X-Hub-Signature-256 header value (optional — validate if present).

        Returns:
            Number of messages processed.
        """
        if raw_signature:
            self._verify_signature(json.dumps(payload).encode(), raw_signature)

        processed = 0
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    self._process_inbound_message(msg, value)
                    processed += 1
                for status in value.get("statuses", []):
                    self._update_delivery_status(status)

        return processed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_inbound_message(self, msg: dict, value: dict) -> WhatsAppMessage:
        """Persist an inbound message and link it to a contact."""
        from_number = msg.get("from", "")
        wa_id = msg.get("id", "")
        msg_type = msg.get("type", "text")
        body_text: Optional[str] = None
        media_url: Optional[str] = None

        if msg_type == "text":
            body_text = msg.get("text", {}).get("body")
        elif msg_type in ("image", "document", "audio", "video"):
            media_url = msg.get(msg_type, {}).get("link")

        # Try to resolve contact from phone number
        contact = self.contact_repo.get_by_whatsapp(from_number) or \
                  self.contact_repo.get_by_phone(from_number)

        # If no contact found, auto-create one (WhatsApp as source)
        if not contact:
            from app.models.contact import ContactSource
            contact = self.contact_repo.create({
                "first_name": from_number,
                "whatsapp_number": from_number,
                "source": ContactSource.WHATSAPP,
            })

        # Get our phone number from metadata
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID or ""
        to_number = value.get("metadata", {}).get("phone_number_id", phone_id)

        record = WhatsAppMessage(
            workspace_id=self.workspace_id,
            contact_id=contact.id,
            wa_message_id=wa_id,
            direction=MessageDirection.INBOUND,
            message_type=MessageType(msg_type) if msg_type in MessageType._value2member_map_ else MessageType.TEXT,
            status=MessageStatus.READ,
            from_number=from_number,
            to_number=to_number,
            body=body_text,
            media_url=media_url,
            raw_payload=msg,
        )
        self.db.add(record)

        # Update contact's last_contacted_at
        contact.last_contacted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(record)

        log.info("whatsapp.inbound", from_number=from_number, message_id=record.id)
        return record

    def _update_delivery_status(self, status: dict) -> None:
        """Update delivery/read status for an outbound message."""
        wa_id = status.get("id")
        new_status = status.get("status", "")
        ts = status.get("timestamp")

        msg = (
            self.db.query(WhatsAppMessage)
            .filter(WhatsAppMessage.wa_message_id == wa_id)
            .first()
        )
        if not msg:
            return

        if new_status == "sent":
            msg.status = MessageStatus.SENT
            msg.sent_at = datetime.now(timezone.utc)
        elif new_status == "delivered":
            msg.status = MessageStatus.DELIVERED
            msg.delivered_at = datetime.now(timezone.utc)
        elif new_status == "read":
            msg.status = MessageStatus.READ
            msg.read_at = datetime.now(timezone.utc)
        elif new_status == "failed":
            msg.status = MessageStatus.FAILED

        self.db.commit()

    def _persist_outbound(
        self,
        to_number: str,
        body: Optional[str],
        message_type: MessageType,
        wa_message_id: Optional[str] = None,
        template_name: Optional[str] = None,
        contact_id: Optional[str] = None,
    ) -> WhatsAppMessage:
        """Store an outbound message in the DB."""
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID or "unknown"
        record = WhatsAppMessage(
            workspace_id=self.workspace_id,
            contact_id=contact_id,
            wa_message_id=wa_message_id,
            direction=MessageDirection.OUTBOUND,
            message_type=message_type,
            status=MessageStatus.SENT if wa_message_id else MessageStatus.FAILED,
            from_number=phone_id,
            to_number=to_number,
            body=body,
            template_name=template_name,
            sent_at=datetime.now(timezone.utc) if wa_message_id else None,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _verify_signature(self, body: bytes, signature_header: str) -> None:
        """Validate Meta's HMAC-SHA256 signature."""
        secret = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN or ""
        expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature_header):
            raise IntegrationError("WhatsApp", "Webhook signature verification failed.")
