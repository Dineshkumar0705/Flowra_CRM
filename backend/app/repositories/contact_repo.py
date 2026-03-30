"""Contact repository."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.contact import Contact, ContactSource

log = logging.getLogger("flowra.repo.contact")


class ContactRepository:
    """CRUD for the Contact table, workspace-scoped."""

    def __init__(self, db: Session, workspace_id: str) -> None:
        self.db = db
        self.workspace_id = workspace_id

    def _base_q(self):
        return self.db.query(Contact).filter(
            Contact.workspace_id == self.workspace_id,
            Contact.deleted_at.is_(None),
        )

    def create(self, data: dict) -> Contact:
        data["workspace_id"] = self.workspace_id
        contact = Contact(**data)
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get_by_id(self, contact_id: str) -> Optional[Contact]:
        return self._base_q().filter(Contact.id == contact_id).first()

    def get_by_email(self, email: str) -> Optional[Contact]:
        return self._base_q().filter(Contact.email == email.lower()).first()

    def get_by_phone(self, phone: str) -> Optional[Contact]:
        return self._base_q().filter(Contact.phone == phone).first()

    def get_by_whatsapp(self, number: str) -> Optional[Contact]:
        return self._base_q().filter(Contact.whatsapp_number == number).first()

    def list(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        source: Optional[ContactSource] = None,
        company_name: Optional[str] = None,
        tag: Optional[str] = None,
        min_lead_score: Optional[int] = None,
    ) -> Tuple[List[Contact], int]:
        q = self._base_q()

        if search:
            term = f"%{search}%"
            q = q.filter(
                or_(
                    Contact.first_name.ilike(term),
                    Contact.last_name.ilike(term),
                    Contact.email.ilike(term),
                    Contact.company_name.ilike(term),
                    Contact.phone.ilike(term),
                )
            )

        if source:
            q = q.filter(Contact.source == source)

        if company_name:
            q = q.filter(Contact.company_name.ilike(f"%{company_name}%"))

        if min_lead_score is not None:
            q = q.filter(Contact.lead_score >= min_lead_score)

        # Tag filtering via JSON array containment — works with PostgreSQL JSONB
        if tag:
            q = q.filter(Contact.tags.contains([tag.lower()]))

        total = q.count()
        items = q.order_by(Contact.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update(self, contact: Contact, data: dict) -> Contact:
        from datetime import datetime, timezone
        for k, v in data.items():
            if hasattr(contact, k):
                setattr(contact, k, v)
        contact.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def soft_delete(self, contact: Contact) -> None:
        contact.soft_delete()
        self.db.commit()
