"""Contact CRUD service with lead-scoring."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.contact import Contact
from app.repositories.contact_repo import ContactRepository
from app.schemas.contact import ContactCreate, ContactListFilters, ContactUpdate

log = logging.getLogger("flowra.service.contact")


class ContactService:
    """Business logic for Contact management."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.repo = ContactRepository(db, workspace_id)
        self.workspace_id = workspace_id

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, payload: ContactCreate, created_by: Optional[str] = None) -> Contact:
        """
        Create a new contact.

        Raises:
            ConflictError: If a contact with the same email already exists in this workspace.
        """
        if payload.email:
            existing = self.repo.get_by_email(str(payload.email))
            if existing:
                raise ConflictError("Contact", f"A contact with email '{payload.email}' already exists.")

        data = payload.model_dump(exclude_unset=False)
        data["created_by"] = created_by

        if payload.email:
            data["email"] = str(payload.email).lower()

        # Initial AI lead score
        data["lead_score"] = self._calculate_lead_score(data)

        contact = self.repo.create(data)
        log.info("contact.created", workspace=self.workspace_id, contact_id=contact.id)
        return contact

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, contact_id: str) -> Contact:
        contact = self.repo.get_by_id(contact_id)
        if not contact:
            raise NotFoundError("Contact", contact_id)
        return contact

    def list(
        self,
        filters: ContactListFilters,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Contact], int]:
        skip = (page - 1) * per_page
        return self.repo.list(
            skip=skip,
            limit=per_page,
            search=filters.search,
            source=filters.source,
            company_name=filters.company_name,
            tag=filters.tag,
            min_lead_score=filters.min_lead_score,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, contact_id: str, payload: ContactUpdate) -> Contact:
        contact = self.get(contact_id)
        data = payload.model_dump(exclude_unset=True)

        if "email" in data and data["email"]:
            data["email"] = str(data["email"]).lower()
            existing = self.repo.get_by_email(data["email"])
            if existing and existing.id != contact_id:
                raise ConflictError("Contact", f"Email '{data['email']}' is already in use.")

        updated = self.repo.update(contact, data)
        log.info("contact.updated", contact_id=contact_id)
        return updated

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, contact_id: str) -> None:
        contact = self.get(contact_id)
        self.repo.soft_delete(contact)
        log.info("contact.deleted", contact_id=contact_id)

    # ------------------------------------------------------------------
    # Lead scoring (rule-based, easily upgradable to ML)
    # ------------------------------------------------------------------

    def _calculate_lead_score(self, data: dict) -> int:
        score = 0
        if data.get("email"):
            score += 20
        if data.get("phone") or data.get("whatsapp_number"):
            score += 15
        if data.get("company_name"):
            score += 10
        if data.get("job_title"):
            score += 5
        if data.get("custom_fields"):
            score += 5
        return min(score, 100)

    def recalculate_lead_score(self, contact_id: str) -> int:
        contact = self.get(contact_id)
        score = self._calculate_lead_score({
            "email": contact.email,
            "phone": contact.phone,
            "whatsapp_number": contact.whatsapp_number,
            "company_name": contact.company_name,
            "job_title": contact.job_title,
            "custom_fields": contact.custom_fields,
        })
        self.repo.update(contact, {"lead_score": score})
        return score
