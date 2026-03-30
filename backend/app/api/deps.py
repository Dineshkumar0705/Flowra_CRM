"""
FastAPI dependency injection — authentication, DB session, pagination.

All protected routes use:
    current_user: Annotated[User, Depends(get_current_user)]
    workspace_id: Annotated[str, Depends(get_workspace_id)]

Role-based helpers:
    require_admin(member)  → raises ForbiddenError if not admin/owner
    require_owner(member)  → raises ForbiddenError if not owner
"""

from typing import Annotated, Optional

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.models.user import User
from app.models.workspace import WorkspaceMember

# ---------------------------------------------------------------------------
# Bearer token scheme (auto-extract from Authorization header)
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# TokenPayload — lightweight wrapper around the decoded JWT dict
# ---------------------------------------------------------------------------


class TokenPayload:
    """Typed wrapper around a decoded JWT payload dict."""

    def __init__(self, payload: dict) -> None:
        self.sub: str = str(payload.get("sub", ""))
        self.workspace_id: Optional[str] = payload.get("workspace_id")
        self.role: Optional[str] = payload.get("role")
        self.token_type: Optional[str] = payload.get("type")

    def is_access_token(self) -> bool:
        return self.token_type == "access"

    def is_refresh_token(self) -> bool:
        return self.token_type == "refresh"


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

DbDep = Annotated[Session, Depends(get_db)]


# ---------------------------------------------------------------------------
# Token extraction
# ---------------------------------------------------------------------------


def _get_token_payload(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(_bearer)
    ] = None,
) -> TokenPayload:
    """Decode the JWT and return its payload. Raises UnauthorizedError on failure."""
    if credentials is None:
        raise UnauthorizedError("Authentication credentials not provided.")
    try:
        raw = decode_token(credentials.credentials)
    except ValueError as exc:
        raise UnauthorizedError(str(exc))
    payload = TokenPayload(raw)
    if not payload.is_access_token():
        raise UnauthorizedError("A valid access token is required.")
    return payload


TokenDep = Annotated[TokenPayload, Depends(_get_token_payload)]


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------


def get_current_user(
    db: DbDep,
    payload: TokenDep,
) -> User:
    """
    Load the authenticated user from the DB.

    Raises UnauthorizedError if the token is invalid or the user is not found.
    """
    if not payload.sub:
        raise UnauthorizedError("Token subject is missing.")

    user = db.query(User).filter(
        User.id == payload.sub,
        User.deleted_at.is_(None),
    ).first()

    if not user:
        raise UnauthorizedError("User not found or deactivated.")

    if not user.is_active:
        raise UnauthorizedError("Account is inactive.")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# Workspace ID (from JWT payload)
# ---------------------------------------------------------------------------


def get_workspace_id(payload: TokenDep) -> str:
    """
    Extract workspace_id from the JWT payload.

    Raises UnauthorizedError if workspace_id is missing.
    """
    if not payload.workspace_id:
        raise UnauthorizedError("Token does not include a workspace context.")
    return payload.workspace_id


WorkspaceIdDep = Annotated[str, Depends(get_workspace_id)]


# ---------------------------------------------------------------------------
# Workspace membership verification
# ---------------------------------------------------------------------------


def get_workspace_member(
    db: DbDep,
    current_user: CurrentUserDep,
    workspace_id: WorkspaceIdDep,
) -> WorkspaceMember:
    """
    Verify the current user is an active member of the token's workspace.

    Returns the WorkspaceMember row (contains the user's role).
    Raises ForbiddenError if not a member.
    """
    member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id,
    ).first()

    if not member:
        raise ForbiddenError("You are not a member of this workspace.")

    return member


WorkspaceMemberDep = Annotated[WorkspaceMember, Depends(get_workspace_member)]


# ---------------------------------------------------------------------------
# Role-based access helpers
# ---------------------------------------------------------------------------


def require_admin(member: WorkspaceMemberDep) -> WorkspaceMember:
    """Require the user to be an owner or admin. Raises ForbiddenError otherwise."""
    # MemberRole is a str enum: .value is "owner"/"admin"/"member"
    role_val = member.role.value if hasattr(member.role, "value") else str(member.role)
    if role_val not in ("owner", "admin"):
        raise ForbiddenError("This action requires admin or owner privileges.")
    return member


def require_owner(member: WorkspaceMemberDep) -> WorkspaceMember:
    """Require the user to be the workspace owner. Raises ForbiddenError otherwise."""
    role_val = member.role.value if hasattr(member.role, "value") else str(member.role)
    if role_val != "owner":
        raise ForbiddenError("This action requires owner privileges.")
    return member


AdminDep = Annotated[WorkspaceMember, Depends(require_admin)]
OwnerDep = Annotated[WorkspaceMember, Depends(require_owner)]


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationParams:
    """Standard pagination query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        limit: int = Query(20, ge=1, le=200, description="Items per page"),
    ) -> None:
        self.page = page
        self.limit = limit
        self.skip = (page - 1) * limit


PaginationDep = Annotated[PaginationParams, Depends(PaginationParams)]
