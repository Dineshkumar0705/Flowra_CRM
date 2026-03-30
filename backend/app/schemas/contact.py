"""Contact Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import EmailStr, Field, field_validator

from app.models.contact import ContactSource, LeadStatus
from app.schemas.base import FlowraSchema


class ContactCreate(FlowraSchema):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=30)
    whatsapp_number: Optional[str] = Field(None, max_length=30)
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    source: ContactSource = ContactSource.MANUAL
    lead_status: LeadStatus = LeadStatus.NEW
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    avatar_url: Optional[str] = None

    @field_validator("first_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("tags")
    @classmethod
    def normalise_tags(cls, v: List[str]) -> List[str]:
        return list({tag.strip().lower() for tag in v if tag.strip()})

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.lower().strip()
        return v


class ContactUpdate(FlowraSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    source: Optional[ContactSource] = None
    lead_status: Optional[LeadStatus] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)


class ContactResponse(FlowraSchema):
    id: str
    workspace_id: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp_number: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    source: ContactSource
    lead_status: LeadStatus = LeadStatus.NEW
    lead_score: int
    tags: List[str]
    custom_fields: Dict[str, Any]
    avatar_url: Optional[str] = None
    last_contacted_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ContactListFilters(FlowraSchema):
    search: Optional[str] = None
    source: Optional[ContactSource] = None
    lead_status: Optional[LeadStatus] = None
    company_name: Optional[str] = None
    tag: Optional[str] = None
    min_lead_score: Optional[int] = Field(None, ge=0, le=100)


# Aliases
ContactOut = ContactResponse
