"""Contact routes — CRUD with filtering and lead scoring."""

from typing import Optional

from fastapi import APIRouter, Query, status

from app.api.deps import (
    CurrentUserDep,
    DbDep,
    PaginationDep,
    WorkspaceIdDep,
    WorkspaceMemberDep,
)
from app.core.exceptions import NotFoundError
from app.schemas.base import PaginatedResponse, SuccessResponse, paginated, success
from app.schemas.contact import ContactCreate, ContactListFilters, ContactResponse, ContactUpdate
from app.services.contact_service import ContactService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ContactResponse])
def list_contacts(
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
    pagination: PaginationDep,
    search: Optional[str] = Query(None, description="Search name, email, or phone"),
    source: Optional[str] = Query(None, description="Filter by lead source"),
    lead_status: Optional[str] = Query(None, description="Filter by lead status"),
    company_name: Optional[str] = Query(None, description="Filter by company name"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    min_lead_score: Optional[int] = Query(None, ge=0, le=100),
):
    """List contacts in the workspace with optional filters."""
    svc = ContactService(db, workspace_id)
    filters = ContactListFilters(
        search=search,
        source=source,
        lead_status=lead_status,
        company_name=company_name,
        tag=tag,
        min_lead_score=min_lead_score,
    )
    items, total = svc.list(
        filters=filters,
        page=pagination.page,
        per_page=pagination.limit,
    )
    return paginated(
        [ContactResponse.model_validate(c) for c in items],
        total=total,
        page=pagination.page,
        per_page=pagination.limit,
    )


@router.post("", response_model=SuccessResponse[ContactResponse], status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: ContactCreate,
    workspace_id: WorkspaceIdDep,
    current_user: CurrentUserDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Create a new contact in the workspace."""
    svc = ContactService(db, workspace_id)
    contact = svc.create(payload, created_by=current_user.id)
    return success(ContactResponse.model_validate(contact), message="Contact created.")


@router.get("/{contact_id}", response_model=SuccessResponse[ContactResponse])
def get_contact(
    contact_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Retrieve a single contact by ID."""
    svc = ContactService(db, workspace_id)
    contact = svc.get(contact_id)
    if not contact:
        raise NotFoundError("Contact", contact_id)
    return success(ContactResponse.model_validate(contact))


@router.patch("/{contact_id}", response_model=SuccessResponse[ContactResponse])
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Partially update a contact."""
    svc = ContactService(db, workspace_id)
    contact = svc.update(contact_id, payload)
    return success(ContactResponse.model_validate(contact), message="Contact updated.")


@router.delete("/{contact_id}", response_model=SuccessResponse[None])
def delete_contact(
    contact_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Soft-delete a contact."""
    svc = ContactService(db, workspace_id)
    svc.delete(contact_id)
    return success(None, message="Contact deleted.")


@router.post("/{contact_id}/rescore", response_model=SuccessResponse[ContactResponse])
def rescore_contact(
    contact_id: str,
    workspace_id: WorkspaceIdDep,
    db: DbDep,
    _member: WorkspaceMemberDep,
):
    """Recalculate the AI lead score for a contact."""
    svc = ContactService(db, workspace_id)
    svc.recalculate_lead_score(contact_id)
    contact = svc.get(contact_id)
    return success(ContactResponse.model_validate(contact), message="Lead score updated.")
