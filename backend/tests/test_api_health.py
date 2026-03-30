"""HTTP integration tests — health check and auth endpoints."""

import pytest


class TestHealthEndpoints:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"

    def test_meta_returns_features(self, client):
        resp = client.get("/api/v1/meta")
        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data

    def test_root_returns_service_info(self, client):
        resp = client.get("/")
        assert resp.status_code == 200


class TestAuthEndpoints:
    def test_signup_creates_account(self, client):
        resp = client.post("/api/v1/auth/signup", json={
            "name": "Arjun Dev",
            "email": "arjun@test.com",
            "password": "password123",
            "workspace_name": "Arjun Agency",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert "access_token" in body["data"]

    def test_signup_duplicate_email_returns_409(self, client):
        payload = {
            "name": "Dup User",
            "email": "dup@test.com",
            "password": "password123",
            "workspace_name": "Dup WS",
        }
        client.post("/api/v1/auth/signup", json=payload)
        resp = client.post("/api/v1/auth/signup", json=payload)
        assert resp.status_code == 409

    def test_me_requires_auth(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client, auth_headers):
        headers = {k: v for k, v in auth_headers.items() if k == "Authorization"}
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "email" in data["data"]


class TestDealsEndpoints:
    def test_list_deals_requires_auth(self, client):
        resp = client.get("/api/v1/deals")
        assert resp.status_code == 401

    def test_create_deal(self, client, auth_headers):
        headers = {k: v for k, v in auth_headers.items() if k == "Authorization"}
        resp = client.post("/api/v1/deals", json={
            "title": "New Website Project",
            "value": 50000,
            "currency": "INR",
        }, headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["title"] == "New Website Project"

    def test_list_deals_returns_only_own(self, client, auth_headers):
        headers = {k: v for k, v in auth_headers.items() if k == "Authorization"}
        # Create 2 deals
        client.post("/api/v1/deals", json={"title": "Deal 1", "value": 10000}, headers=headers)
        client.post("/api/v1/deals", json={"title": "Deal 2", "value": 20000}, headers=headers)

        resp = client.get("/api/v1/deals", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta"]["total"] == 2


class TestContactsEndpoints:
    def test_create_and_get_contact(self, client, auth_headers):
        headers = {k: v for k, v in auth_headers.items() if k == "Authorization"}

        create_resp = client.post("/api/v1/contacts", json={
            "first_name": "Neha",
            "last_name": "Patel",
            "email": "neha@example.com",
        }, headers=headers)
        assert create_resp.status_code == 201
        contact_id = create_resp.json()["data"]["id"]

        get_resp = client.get(f"/api/v1/contacts/{contact_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["data"]["email"] == "neha@example.com"
