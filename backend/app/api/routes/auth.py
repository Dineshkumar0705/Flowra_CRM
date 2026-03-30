"""Auth routes — signup, login, token refresh, me, change password."""

from fastapi import APIRouter, status

from app.api.deps import CurrentUserDep, DbDep
from app.schemas.base import SuccessResponse, success
from app.schemas.user import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=SuccessResponse[dict], status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: DbDep):
    """Create a new user account and a default workspace."""
    svc = AuthService(db)
    tokens, user = svc.signup(payload)
    return success(
        {
            **tokens,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
        },
        message="Account created successfully.",
    )


@router.post("/login", response_model=SuccessResponse[dict])
def login(payload: LoginRequest, db: DbDep):
    """
    Authenticate and receive access + refresh tokens.

    Provide workspace_id in the body to log into a specific workspace.
    If omitted, the user's first active workspace is selected automatically.
    """
    svc = AuthService(db)

    # Resolve workspace_id: either from request body or auto-detected
    workspace_id = getattr(payload, "workspace_id", None)
    if not workspace_id:
        # Auto-detect: find user's first active workspace
        from app.repositories.workspace_repo import WorkspaceRepository
        from app.repositories.user_repo import UserRepository
        user_repo = UserRepository(db)
        ws_repo = WorkspaceRepository(db)
        user = user_repo.get_by_email(payload.email)
        if user:
            workspaces = ws_repo.list_for_user(user.id)
            if workspaces:
                workspace_id = workspaces[0].id
        if not workspace_id:
            from app.core.exceptions import UnauthorizedError
            raise UnauthorizedError("Invalid email or password.")

    tokens, user = svc.login(payload, workspace_id)
    return success(
        {
            **tokens,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
        },
        message="Login successful.",
    )


@router.post("/refresh", response_model=SuccessResponse[dict])
def refresh_token(payload: RefreshTokenRequest, db: DbDep):
    """Exchange a valid refresh token for a new access token."""
    svc = AuthService(db)
    result = svc.refresh_tokens(payload.refresh_token)
    return success(result, message="Token refreshed.")


@router.get("/me", response_model=SuccessResponse[UserResponse])
def me(current_user: CurrentUserDep):
    """Return the currently authenticated user's profile."""
    return success(UserResponse.model_validate(current_user))


@router.post("/change-password", response_model=SuccessResponse[None])
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUserDep,
    db: DbDep,
):
    """Change the authenticated user's password."""
    svc = AuthService(db)
    svc.change_password(current_user.id, payload.old_password, payload.new_password)
    return success(None, message="Password changed successfully.")
