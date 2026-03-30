"""Workspace and WorkspaceMember Pydantic schemas."""

import re
from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.models.workspace import MemberRole, WorkspacePlan
from app.schemas.base import FlowraSchema


# ---------------------------------------------------------------------------
# Workspace
# ---------------------------------------------------------------------------

class WorkspaceCreate(FlowraSchema):
    name: str = Field(..., min_length=2, max_length=255, examples=["Acme Agency"])
    slug: Optional[str] = Field(None, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug may only contain lowercase letters, digits, and hyphens.")
        return v

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class WorkspaceUpdate(FlowraSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    logo_url: Optional[str] = None
    settings: Optional[dict] = None


class WorkspaceResponse(FlowraSchema):
    id: str
    name: str
    slug: str
    logo_url: Optional[str]
    plan: WorkspacePlan
    plan_expires_at: Optional[datetime]
    owner_id: str
    settings: dict
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# WorkspaceMember
# ---------------------------------------------------------------------------

class InviteMemberRequest(FlowraSchema):
    email: str = Field(..., description="Email of the user to invite")
    role: MemberRole = MemberRole.MEMBER


class UpdateMemberRoleRequest(FlowraSchema):
    role: MemberRole


class WorkspaceMemberResponse(FlowraSchema):
    id: str
    workspace_id: str
    user_id: str
    role: MemberRole
    is_active: bool
    created_at: datetime

    # Denormalised from User
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None


# ---------------------------------------------------------------------------
# Aliases (used by route handlers)
# ---------------------------------------------------------------------------
WorkspaceOut = WorkspaceResponse
UpdateWorkspaceRequest = WorkspaceUpdate
WorkspaceMemberOut = WorkspaceMemberResponse
AddMemberRequest = InviteMemberRequest
