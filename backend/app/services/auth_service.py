"""
Authentication and user registration service.

Handles:
  - Signup (creates user + workspace in one transaction)
  - Login (validates credentials, issues JWT pair)
  - Token refresh
  - Password change
"""

import logging
import re
import unicodedata
from datetime import timedelta
from typing import Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.workspace import MemberRole, WorkspacePlan
from app.repositories.user_repo import UserRepository
from app.repositories.workspace_repo import WorkspaceRepository
from app.schemas.user import LoginRequest, SignupRequest

log = logging.getLogger("flowra.service.auth")


def _slugify(text: str) -> str:
    """Convert workspace name to a URL-safe slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)[:80]


class AuthService:
    """Business logic for user authentication and account management."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.workspace_repo = WorkspaceRepository(db)

    # ------------------------------------------------------------------
    # Signup — creates user + workspace atomically
    # ------------------------------------------------------------------

    def signup(self, payload: SignupRequest) -> Tuple[dict, dict]:
        """
        Register a new user and create their first workspace.

        Args:
            payload: Validated SignupRequest schema.

        Returns:
            Tuple of (token_dict, user_dict).

        Raises:
            ConflictError: If the email is already registered.
        """
        if self.user_repo.email_exists(payload.email):
            raise ConflictError("User", f"Email '{payload.email}' is already registered.")

        # Create user
        user = self.user_repo.create({
            "name": payload.name,
            "email": payload.email.lower(),
            "hashed_password": hash_password(payload.password),
        })

        # Create workspace
        base_slug = _slugify(payload.workspace_name)
        slug = base_slug
        counter = 1
        while self.workspace_repo.slug_exists(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = self.workspace_repo.create({
            "name": payload.workspace_name,
            "slug": slug,
            "owner_id": user.id,
            "plan": WorkspacePlan.STARTER,
            "settings": {},
        })

        # Add user as workspace owner
        self.workspace_repo.add_member(workspace.id, user.id, MemberRole.OWNER)

        tokens = self._issue_tokens(user.id, workspace.id)
        log.info("auth.signup", user_id=user.id, workspace_id=workspace.id)
        return tokens, user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    def login(self, payload: LoginRequest, workspace_id: str) -> Tuple[dict, dict]:
        """
        Authenticate a user and issue a JWT pair.

        Args:
            payload:      Validated LoginRequest.
            workspace_id: The workspace the user is logging into.

        Returns:
            Tuple of (token_dict, user_dict).

        Raises:
            UnauthorizedError: For any credential failure (intentionally vague).
        """
        user = self.user_repo.get_by_email(payload.email)
        _invalid = UnauthorizedError("Invalid email or password.")

        if user is None:
            raise _invalid

        if user.is_account_locked():
            raise UnauthorizedError("Account is temporarily locked. Try again in 15 minutes.")

        if not verify_password(payload.password, user.hashed_password):
            user.record_login_failure()
            self.db.commit()
            raise _invalid

        if not user.is_active:
            raise UnauthorizedError("Account is inactive.")

        # Verify membership
        member = self.workspace_repo.get_member(workspace_id, user.id)
        if not member or not member.is_active:
            raise UnauthorizedError("You don't have access to this workspace.")

        user.record_login_success()
        self.db.commit()

        tokens = self._issue_tokens(user.id, workspace_id, role=str(member.role))
        log.info("auth.login", user_id=user.id, workspace_id=workspace_id)
        return tokens, user

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Issue a new access token from a valid refresh token.

        Raises:
            UnauthorizedError: If the token is invalid or expired.
        """
        from app.core.security import decode_token, is_refresh_token, extract_user_id

        try:
            payload = decode_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError(str(exc))

        if not is_refresh_token(payload):
            raise UnauthorizedError("Invalid token type.")

        user_id = extract_user_id(payload)
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")

        new_access = create_access_token(user_id=user_id)
        return {
            "access_token": new_access,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    # ------------------------------------------------------------------
    # Change password
    # ------------------------------------------------------------------

    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        """
        Update the user's password after verifying the old one.

        Raises:
            UnauthorizedError: If old_password is wrong.
            ValidationError:   If new_password is too weak.
        """
        from datetime import datetime, timezone

        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedError()

        if not verify_password(old_password, user.hashed_password):
            raise UnauthorizedError("Current password is incorrect.")

        if len(new_password) < 8:
            raise ValidationError("New password must be at least 8 characters.", field="new_password")

        self.user_repo.update(user, {
            "hashed_password": hash_password(new_password),
            "password_updated_at": datetime.now(timezone.utc),
        })
        log.info("auth.password_changed", user_id=user_id)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _issue_tokens(self, user_id: str, workspace_id: str, role: str = "member") -> dict:
        access = create_access_token(user_id=user_id, workspace_id=workspace_id, role=role)
        refresh = create_refresh_token(user_id=user_id)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
