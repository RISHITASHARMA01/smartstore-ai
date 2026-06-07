import pytest

ADMIN_URL = "/admin/users"


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── authentication + authorization ───────────────────────────────────────────

class TestAdminAuth:
    def test_list_requires_auth(self, client):
        assert client.get(ADMIN_URL).status_code in (401, 403)

    def test_get_requires_auth(self, client):
        assert client.get(f"{ADMIN_URL}/1").status_code in (401, 403)

    def test_patch_requires_auth(self, client):
        assert client.patch(f"{ADMIN_URL}/1", json={"role": "staff"}).status_code in (401, 403)

    def test_staff_cannot_list_users(self, client, staff_token):
        assert client.get(ADMIN_URL, headers=auth(staff_token)).status_code == 403

    def test_staff_cannot_get_user(self, client, staff_token):
        assert client.get(f"{ADMIN_URL}/1", headers=auth(staff_token)).status_code == 403

    def test_staff_cannot_patch_user(self, client, staff_token):
        assert client.patch(f"{ADMIN_URL}/1", json={"role": "admin"}, headers=auth(staff_token)).status_code == 403


# ── list users ────────────────────────────────────────────────────────────────

class TestListUsers:
    def test_admin_can_list_users(self, client, admin_token):
        resp = client.get(ADMIN_URL, headers=auth(admin_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1  # at least the admin itself

    def test_list_includes_all_roles(self, client, admin_token, staff_token):
        resp = client.get(ADMIN_URL, headers=auth(admin_token))
        roles = {u["role"] for u in resp.json()}
        assert "admin" in roles
        assert "staff" in roles

    def test_list_search_by_email(self, client, admin_token):
        resp = client.get(ADMIN_URL, params={"search": "admin@test.com"}, headers=auth(admin_token))
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "admin@test.com" in emails

    def test_list_search_no_match(self, client, admin_token):
        resp = client.get(ADMIN_URL, params={"search": "nobody_xyz@example.com"}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_pagination(self, client, admin_token):
        resp = client.get(ADMIN_URL, params={"skip": 0, "limit": 1}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()) <= 1

    def test_list_response_has_no_password(self, client, admin_token):
        resp = client.get(ADMIN_URL, headers=auth(admin_token))
        for user in resp.json():
            assert "password" not in user


# ── get single user ───────────────────────────────────────────────────────────

class TestGetUser:
    def test_admin_can_get_user(self, client, admin_token, db_session):
        from app.models import User
        admin = db_session.query(User).filter(User.email == "admin@test.com").first()
        resp = client.get(f"{ADMIN_URL}/{admin.id}", headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "admin@test.com"

    def test_get_user_not_found(self, client, admin_token):
        resp = client.get(f"{ADMIN_URL}/99999", headers=auth(admin_token))
        assert resp.status_code == 404

    def test_get_response_has_no_password(self, client, admin_token, db_session):
        from app.models import User
        admin = db_session.query(User).filter(User.email == "admin@test.com").first()
        resp = client.get(f"{ADMIN_URL}/{admin.id}", headers=auth(admin_token))
        assert "password" not in resp.json()


# ── update user ───────────────────────────────────────────────────────────────

class TestUpdateUser:
    def test_admin_can_promote_staff_to_admin(self, client, admin_token, staff_token, db_session):
        from app.models import User
        staff = db_session.query(User).filter(User.email == "staff@test.com").first()
        resp = client.patch(f"{ADMIN_URL}/{staff.id}", json={"role": "admin"}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_admin_can_demote_admin_to_staff(self, client, admin_token, db_session):
        from app.models import User
        from app.auth.utils import hash_password
        # create a second admin to demote
        other = User(email="other_admin@test.com", password=hash_password("AdminPass1"), role="admin")
        db_session.add(other)
        db_session.commit()
        db_session.refresh(other)
        resp = client.patch(f"{ADMIN_URL}/{other.id}", json={"role": "staff"}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["role"] == "staff"

    def test_admin_can_deactivate_user(self, client, admin_token, staff_token, db_session):
        from app.models import User
        staff = db_session.query(User).filter(User.email == "staff@test.com").first()
        resp = client.patch(f"{ADMIN_URL}/{staff.id}", json={"is_active": False}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_admin_can_reactivate_user(self, client, admin_token, db_session):
        from app.models import User
        from app.auth.utils import hash_password
        inactive = User(email="inactive@test.com", password=hash_password("Pass1234"), role="staff", is_active=False)
        db_session.add(inactive)
        db_session.commit()
        db_session.refresh(inactive)
        resp = client.patch(f"{ADMIN_URL}/{inactive.id}", json={"is_active": True}, headers=auth(admin_token))
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_admin_cannot_change_own_role(self, client, admin_token, db_session):
        from app.models import User
        admin = db_session.query(User).filter(User.email == "admin@test.com").first()
        resp = client.patch(f"{ADMIN_URL}/{admin.id}", json={"role": "staff"}, headers=auth(admin_token))
        assert resp.status_code == 400
        assert "role" in resp.json()["detail"].lower()

    def test_admin_cannot_deactivate_self(self, client, admin_token, db_session):
        from app.models import User
        admin = db_session.query(User).filter(User.email == "admin@test.com").first()
        resp = client.patch(f"{ADMIN_URL}/{admin.id}", json={"is_active": False}, headers=auth(admin_token))
        assert resp.status_code == 400
        assert "deactivate" in resp.json()["detail"].lower()

    def test_update_user_not_found(self, client, admin_token):
        resp = client.patch(f"{ADMIN_URL}/99999", json={"role": "staff"}, headers=auth(admin_token))
        assert resp.status_code == 404

    def test_invalid_role_rejected(self, client, admin_token, staff_token, db_session):
        from app.models import User
        staff = db_session.query(User).filter(User.email == "staff@test.com").first()
        resp = client.patch(f"{ADMIN_URL}/{staff.id}", json={"role": "superuser"}, headers=auth(admin_token))
        assert resp.status_code == 422
