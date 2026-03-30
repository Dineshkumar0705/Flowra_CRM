"""Tests for JWT token creation and validation."""

import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "mysecretpassword123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_is_bcrypt(self):
        hashed = hash_password("any")
        assert hashed.startswith("$2b$")


class TestJWTTokens:
    def test_access_token_contains_user_and_workspace(self):
        token = create_access_token(
            user_id="user-123",
            workspace_id="ws-456",
            role="owner",
        )
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["workspace_id"] == "ws-456"
        assert payload["role"] == "owner"
        assert payload["type"] == "access"

    def test_refresh_token_type(self):
        token = create_refresh_token(user_id="user-123")
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == "user-123"
        assert "workspace_id" not in payload

    def test_decode_invalid_token_raises(self):
        with pytest.raises(ValueError):
            decode_token("this.is.not.valid")

    def test_decode_tampered_token_raises(self):
        token = create_access_token("u1", "w1")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(ValueError):
            decode_token(tampered)
