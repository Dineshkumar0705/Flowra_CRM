"""Tests for AuthService — signup, login, token refresh, password change."""

import pytest

from app.services.auth_service import AuthService
from app.schemas.user import LoginRequest, SignupRequest
from app.core.exceptions import ConflictError, UnauthorizedError


@pytest.fixture()
def signup_payload():
    return SignupRequest(
        name="Priya Sharma",
        email="priya@example.com",
        password="securePass123",
        workspace_name="Priya's Agency",
    )


class TestSignup:
    def test_signup_creates_user_workspace_member(self, db, signup_payload):
        svc = AuthService(db)
        tokens, user = svc.signup(signup_payload)

        assert user.id is not None
        assert user.email == "priya@example.com"
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["token_type"] == "bearer"

    def test_signup_normalises_email(self, db):
        svc = AuthService(db)
        payload = SignupRequest(
            name="Test",
            email="TEST@EXAMPLE.COM",
            password="testpass123",
            workspace_name="Test WS",
        )
        _, user = svc.signup(payload)
        assert user.email == "test@example.com"

    def test_duplicate_email_raises_conflict(self, db, signup_payload):
        svc = AuthService(db)
        svc.signup(signup_payload)

        with pytest.raises(ConflictError):
            svc.signup(signup_payload)


class TestLogin:
    def test_login_success(self, db, signup_payload):
        svc = AuthService(db)
        _, user = svc.signup(signup_payload)

        # Get workspace_id from the token
        from app.repositories.workspace_repo import WorkspaceRepository
        ws_repo = WorkspaceRepository(db)
        workspaces = ws_repo.list_for_user(user.id)
        workspace_id = workspaces[0].id

        tokens, logged_user = svc.login(
            LoginRequest(email="priya@example.com", password="securePass123"),
            workspace_id=workspace_id,
        )
        assert tokens["access_token"]
        assert logged_user.id == user.id

    def test_wrong_password_raises(self, db, signup_payload):
        svc = AuthService(db)
        _, user = svc.signup(signup_payload)

        from app.repositories.workspace_repo import WorkspaceRepository
        workspaces = WorkspaceRepository(db).list_for_user(user.id)

        with pytest.raises(UnauthorizedError):
            svc.login(
                LoginRequest(email="priya@example.com", password="WRONG"),
                workspace_id=workspaces[0].id,
            )

    def test_nonexistent_user_raises(self, db):
        svc = AuthService(db)
        with pytest.raises(UnauthorizedError):
            svc.login(
                LoginRequest(email="nobody@example.com", password="pass"),
                workspace_id="some-ws-id",
            )


class TestTokenRefresh:
    def test_refresh_returns_new_access_token(self, db, signup_payload):
        svc = AuthService(db)
        tokens, _ = svc.signup(signup_payload)

        result = svc.refresh_tokens(tokens["refresh_token"])
        assert result["access_token"]
        assert result["access_token"] != tokens["access_token"]

    def test_refresh_with_access_token_raises(self, db, signup_payload):
        svc = AuthService(db)
        tokens, _ = svc.signup(signup_payload)

        with pytest.raises(UnauthorizedError):
            svc.refresh_tokens(tokens["access_token"])


class TestChangePassword:
    def test_change_password_success(self, db, signup_payload):
        svc = AuthService(db)
        _, user = svc.signup(signup_payload)

        # Should not raise
        svc.change_password(user.id, "securePass123", "newPass456!")

    def test_wrong_old_password_raises(self, db, signup_payload):
        svc = AuthService(db)
        _, user = svc.signup(signup_payload)

        with pytest.raises(UnauthorizedError):
            svc.change_password(user.id, "WRONG_OLD", "newPass456!")
