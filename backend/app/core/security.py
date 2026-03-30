"""
Flowra security utilities.

Responsibilities:
  - bcrypt password hashing / verification
  - JWT access-token and refresh-token creation
  - Token decoding and validation
  - Workspace-scoped token payloads (UUID-safe)

All token subjects are stored as strings (UUID or integer as str) so the
same code works regardless of whether IDs are UUIDs or integers.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

log = logging.getLogger("flowra.security")

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Internal token builder
# ---------------------------------------------------------------------------

def _build_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT.

    Args:
        subject:      The token subject — always a string (UUID.hex or str(int)).
        token_type:   "access" or "refresh".
        expires_delta: How long the token is valid.
        extra:        Additional claims merged into the payload.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ---------------------------------------------------------------------------
# Public token creators
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: str,
    workspace_id: Optional[str] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a short-lived access token.

    Args:
        user_id:      String representation of the user's UUID.
        workspace_id: Active workspace UUID as string (for multi-tenancy).
        role:         User's role within the workspace.
        expires_delta: Override the default ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        Signed JWT string.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _build_token(
        subject=user_id,
        token_type="access",
        expires_delta=delta,
        extra={"workspace_id": workspace_id, "role": role},
    )


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a long-lived refresh token.

    The refresh token carries only the minimal subject claim — no workspace
    or role — because it is used only to issue new access tokens.

    Args:
        user_id: String representation of the user's UUID.

    Returns:
        Signed JWT string.
    """
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _build_token(subject=user_id, token_type="refresh", expires_delta=delta)


# ---------------------------------------------------------------------------
# Token decoding
# ---------------------------------------------------------------------------

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT.

    Args:
        token: Raw JWT string from the Authorization header.

    Returns:
        Decoded payload dict.

    Raises:
        ValueError: If the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise ValueError(f"Token invalid or expired: {exc}") from exc


def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Silently decode a token.

    Returns the payload dict on success, or None if the token is invalid.
    Useful in middleware where a missing/invalid token is not necessarily
    an error.
    """
    try:
        return decode_token(token)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Convenience extractors
# ---------------------------------------------------------------------------

def extract_user_id(payload: Dict[str, Any]) -> str:
    """Return the 'sub' claim from a decoded token payload."""
    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token payload missing 'sub' claim.")
    return str(sub)


def extract_workspace_id(payload: Dict[str, Any]) -> Optional[str]:
    """Return the workspace_id claim, or None if absent."""
    return payload.get("workspace_id")


def extract_role(payload: Dict[str, Any]) -> Optional[str]:
    """Return the role claim, or None if absent."""
    return payload.get("role")


def is_access_token(payload: Dict[str, Any]) -> bool:
    return payload.get("type") == "access"


def is_refresh_token(payload: Dict[str, Any]) -> bool:
    return payload.get("type") == "refresh"


# ---------------------------------------------------------------------------
# Refresh flow
# ---------------------------------------------------------------------------

def rotate_access_token(refresh_token: str) -> str:
    """
    Issue a new access token from a valid refresh token.

    Args:
        refresh_token: A valid refresh JWT.

    Returns:
        New access token string.

    Raises:
        ValueError: If the refresh token is invalid or is not of type 'refresh'.
    """
    payload = decode_token(refresh_token)
    if not is_refresh_token(payload):
        raise ValueError("Provided token is not a refresh token.")

    user_id = extract_user_id(payload)
    return create_access_token(user_id=user_id)
