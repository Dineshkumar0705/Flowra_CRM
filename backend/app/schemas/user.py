"""User, Auth, and token Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import EmailStr, Field, field_validator

from app.models.user import UserRole
from app.schemas.base import FlowraSchema


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class SignupRequest(FlowraSchema):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    workspace_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class LoginRequest(FlowraSchema):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(FlowraSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int   # seconds


class RefreshTokenRequest(FlowraSchema):
    refresh_token: str


class ChangePasswordRequest(FlowraSchema):
    old_password: str
    new_password: str = Field(..., min_length=8)


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

class UserCreate(FlowraSchema):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.SALES

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class UserUpdate(FlowraSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    avatar_url: Optional[str] = None
    role: Optional[UserRole] = None
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class UserResponse(FlowraSchema):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_verified: bool
    is_superuser: bool
    last_login: Optional[datetime] = None
    login_count: int
    preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Aliases (used by route handlers)
# ---------------------------------------------------------------------------
UserOut = UserResponse
LoginResponse = TokenResponse
RefreshRequest = RefreshTokenRequest
