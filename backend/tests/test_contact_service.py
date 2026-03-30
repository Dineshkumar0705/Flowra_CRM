"""Tests for ContactService business logic."""

import uuid
import pytest

from app.services.contact_service import ContactService
from app.schemas.contact import ContactCreate, ContactUpdate
from app.core.exceptions import ConflictError, NotFoundError


class TestContactCreate:
    def test_create_contact(self, db, make_workspace, make_user):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        svc = ContactService(db, ws.id)

        payload = ContactCreate(
            first_name="Rahul",
            last_name="Sharma",
            email="rahul@example.com",
            phone="+919876543210",
        )
        contact = svc.create(payload, created_by=user.id)

        assert contact.id is not None
        assert contact.workspace_id == ws.id
        assert contact.email == "rahul@example.com"
        assert contact.lead_score >= 0

    def test_duplicate_email_raises_conflict(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        make_contact(workspace_id=ws.id, email="dup@example.com")

        svc = ContactService(db, ws.id)
        payload = ContactCreate(
            first_name="Another",
            last_name="Person",
            email="dup@example.com",
        )
        with pytest.raises(ConflictError):
            svc.create(payload)

    def test_same_email_different_workspace_ok(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws1 = make_workspace(owner_id=user.id, name="WS1")
        ws2 = make_workspace(owner_id=user.id, name="WS2")
        make_contact(workspace_id=ws1.id, email="shared@example.com")

        svc2 = ContactService(db, ws2.id)
        payload = ContactCreate(first_name="X", last_name="Y", email="shared@example.com")
        contact = svc2.create(payload)
        assert contact.workspace_id == ws2.id


class TestContactLeadScore:
    def test_score_increases_with_data(self, db, make_workspace, make_user):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        svc = ContactService(db, ws.id)

        # Minimal data
        c1 = svc.create(ContactCreate(first_name="Min", last_name="Data"))
        score_min = c1.lead_score

        # Full data
        c2 = svc.create(ContactCreate(
            first_name="Full",
            last_name="Data",
            email="full@example.com",
            phone="+919876543210",
            company_name="Acme Inc",
            job_title="CEO",
            whatsapp_number="+919876543210",
        ))
        score_full = c2.lead_score

        assert score_full > score_min

    def test_score_capped_at_100(self, db, make_workspace, make_user):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        svc = ContactService(db, ws.id)

        contact = svc.create(ContactCreate(
            first_name="A", last_name="B",
            email="a@b.com", phone="+91999",
            company_name="Co", job_title="CEO",
            whatsapp_number="+91999",
        ))
        assert contact.lead_score <= 100


class TestContactGet:
    def test_get_existing(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        contact = make_contact(ws.id)

        svc = ContactService(db, ws.id)
        result = svc.get(contact.id)
        assert result is not None
        assert result.id == contact.id

    def test_get_nonexistent_returns_none(self, db, make_workspace, make_user):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        svc = ContactService(db, ws.id)
        result = svc.get(str(uuid.uuid4()))
        assert result is None

    def test_get_wrong_workspace_returns_none(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws1 = make_workspace(owner_id=user.id, name="W1")
        ws2 = make_workspace(owner_id=user.id, name="W2")
        contact = make_contact(ws1.id)

        svc2 = ContactService(db, ws2.id)
        result = svc2.get(contact.id)
        assert result is None   # Multi-tenancy isolation


class TestContactUpdate:
    def test_update_fields(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        contact = make_contact(ws.id)
        svc = ContactService(db, ws.id)

        updated = svc.update(contact.id, ContactUpdate(company_name="New Corp"))
        assert updated.company_name == "New Corp"


class TestContactDelete:
    def test_soft_delete(self, db, make_workspace, make_user, make_contact):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        contact = make_contact(ws.id)
        svc = ContactService(db, ws.id)

        svc.delete(contact.id)
        result = svc.get(contact.id)
        assert result is None   # Soft-deleted contacts are not returned

    def test_delete_nonexistent_raises(self, db, make_workspace, make_user):
        user = make_user()
        ws = make_workspace(owner_id=user.id)
        svc = ContactService(db, ws.id)

        with pytest.raises(NotFoundError):
            svc.delete(str(uuid.uuid4()))
