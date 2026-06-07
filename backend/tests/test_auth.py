import pytest


REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"
REFRESH_URL = "/auth/refresh"
ME_URL = "/auth/me"

VALID_USER = {
    "email": "newuser@example.com",
    "password": "ValidPass1",
}


class TestRegister:
    def test_register_user(self, client):
        resp = client.post(REGISTER_URL, json=VALID_USER)
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == VALID_USER["email"]
        assert body["role"] == "staff"
        assert "id" in body
        assert "password" not in body

    def test_register_duplicate_email(self, client):
        client.post(REGISTER_URL, json=VALID_USER)
        resp = client.post(REGISTER_URL, json=VALID_USER)
        assert resp.status_code == 400
        assert "already registered" in resp.json()["detail"].lower()

    def test_register_forces_staff_role(self, client):
        payload = {**VALID_USER, "email": "tryingadmin@example.com", "role": "admin"}
        resp = client.post(REGISTER_URL, json=payload)
        assert resp.status_code == 201
        assert resp.json()["role"] == "staff"

    def test_register_weak_password(self, client):
        resp = client.post(REGISTER_URL, json={"email": "weak@example.com", "password": "short"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client, db_session):
        client.post(REGISTER_URL, json=VALID_USER)
        resp = client.post(LOGIN_URL, json=VALID_USER)
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == VALID_USER["email"]

    def test_login_wrong_password(self, client):
        client.post(REGISTER_URL, json=VALID_USER)
        resp = client.post(LOGIN_URL, json={**VALID_USER, "password": "WrongPass1"})
        assert resp.status_code == 401

    def test_login_wrong_email(self, client):
        resp = client.post(LOGIN_URL, json={"email": "nobody@example.com", "password": "ValidPass1"})
        assert resp.status_code == 401

    def test_login_returns_user_object(self, client):
        client.post(REGISTER_URL, json=VALID_USER)
        resp = client.post(LOGIN_URL, json=VALID_USER)
        user = resp.json()["user"]
        assert user["email"] == VALID_USER["email"]
        assert "role" in user
        assert "is_active" in user


class TestRefreshToken:
    def test_refresh_token(self, client):
        client.post(REGISTER_URL, json=VALID_USER)
        login_resp = client.post(LOGIN_URL, json=VALID_USER)
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(REFRESH_URL, json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    def test_refresh_with_invalid_token(self, client):
        resp = client.post(REFRESH_URL, json={"refresh_token": "not.a.valid.token"})
        assert resp.status_code == 401

    def test_refresh_with_access_token_rejected(self, client):
        client.post(REGISTER_URL, json=VALID_USER)
        login_resp = client.post(LOGIN_URL, json=VALID_USER)
        access_token = login_resp.json()["access_token"]

        resp = client.post(REFRESH_URL, json={"refresh_token": access_token})
        assert resp.status_code == 401


class TestProtectedRoutes:
    def test_access_protected_route(self, client, staff_token):
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {staff_token}"})
        assert resp.status_code == 200
        assert "email" in resp.json()

    def test_access_protected_route_no_token(self, client):
        resp = client.get(ME_URL)
        assert resp.status_code in (401, 403)

    def test_access_protected_route_invalid_token(self, client):
        resp = client.get(ME_URL, headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401

    def test_me_returns_correct_user(self, client, staff_token):
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {staff_token}"})
        body = resp.json()
        assert body["email"] == "staff@test.com"
        assert body["role"] == "staff"
        assert body["is_active"] is True
