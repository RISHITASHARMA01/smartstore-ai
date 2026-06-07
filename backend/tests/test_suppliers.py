import pytest

SUPPLIERS_URL = "/suppliers"

VALID_SUPPLIER = {
    "name": "Fresh Foods Co.",
    "email": "contact@freshfoods.com",
    "categories": ["Dairy", "Produce"],
    "lead_time_days": 3,
}


# ── helpers ───────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_supplier(client, token, overrides=None):
    payload = {**VALID_SUPPLIER, **(overrides or {})}
    resp = client.post(SUPPLIERS_URL, json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.json()
    return resp.json()


# ── authentication guard ──────────────────────────────────────────────────────

class TestSuppliersAuth:
    def test_list_requires_auth(self, client):
        assert client.get(SUPPLIERS_URL).status_code in (401, 403)

    def test_get_requires_auth(self, client):
        assert client.get(f"{SUPPLIERS_URL}/1").status_code in (401, 403)

    def test_create_requires_auth(self, client):
        assert client.post(SUPPLIERS_URL, json=VALID_SUPPLIER).status_code in (401, 403)

    def test_update_requires_auth(self, client):
        assert client.put(f"{SUPPLIERS_URL}/1", json={"name": "x"}).status_code in (401, 403)

    def test_delete_requires_auth(self, client):
        assert client.delete(f"{SUPPLIERS_URL}/1").status_code in (401, 403)


# ── create ────────────────────────────────────────────────────────────────────

class TestCreateSupplier:
    def test_create_supplier(self, client, staff_token):
        resp = client.post(SUPPLIERS_URL, json=VALID_SUPPLIER, headers=auth(staff_token))
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == VALID_SUPPLIER["name"]
        assert body["email"] == VALID_SUPPLIER["email"]
        assert body["categories"] == VALID_SUPPLIER["categories"]
        assert body["lead_time_days"] == VALID_SUPPLIER["lead_time_days"]
        assert body["is_active"] is True
        assert "id" in body
        assert "created_at" in body

    def test_create_duplicate_email(self, client, staff_token):
        create_supplier(client, staff_token)
        resp = client.post(SUPPLIERS_URL, json=VALID_SUPPLIER, headers=auth(staff_token))
        assert resp.status_code == 400
        assert "email" in resp.json()["detail"].lower()

    def test_create_missing_name(self, client, staff_token):
        payload = {**VALID_SUPPLIER}
        del payload["name"]
        resp = client.post(SUPPLIERS_URL, json=payload, headers=auth(staff_token))
        assert resp.status_code == 422

    def test_create_invalid_email(self, client, staff_token):
        resp = client.post(
            SUPPLIERS_URL,
            json={**VALID_SUPPLIER, "email": "not-an-email"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_create_negative_lead_time(self, client, staff_token):
        resp = client.post(
            SUPPLIERS_URL,
            json={**VALID_SUPPLIER, "email": "other@test.com", "lead_time_days": -1},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_create_defaults_categories_and_lead_time(self, client, staff_token):
        payload = {"name": "Minimal Supplier", "email": "minimal@test.com"}
        resp = client.post(SUPPLIERS_URL, json=payload, headers=auth(staff_token))
        assert resp.status_code == 201
        body = resp.json()
        assert body["categories"] == []
        assert body["lead_time_days"] == 3

    def test_create_empty_name_rejected(self, client, staff_token):
        resp = client.post(
            SUPPLIERS_URL,
            json={**VALID_SUPPLIER, "email": "empty@test.com", "name": ""},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422


# ── list ──────────────────────────────────────────────────────────────────────

class TestListSuppliers:
    def test_list_suppliers(self, client, staff_token):
        create_supplier(client, staff_token)
        resp = client.get(SUPPLIERS_URL, headers=auth(staff_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_search_by_name(self, client, staff_token):
        create_supplier(client, staff_token, {"name": "Organic Valley Farm", "email": "organic@test.com"})
        resp = client.get(SUPPLIERS_URL, params={"search": "Organic"}, headers=auth(staff_token))
        assert resp.status_code == 200
        names = [s["name"] for s in resp.json()]
        assert any("Organic" in n for n in names)

    def test_list_search_by_email(self, client, staff_token):
        create_supplier(client, staff_token, {"name": "Email Search Supplier", "email": "uniquemail99@test.com"})
        resp = client.get(SUPPLIERS_URL, params={"search": "uniquemail99"}, headers=auth(staff_token))
        assert resp.status_code == 200
        emails = [s["email"] for s in resp.json()]
        assert "uniquemail99@test.com" in emails

    def test_list_pagination(self, client, staff_token):
        for i in range(5):
            create_supplier(client, staff_token, {"name": f"Paginate Supplier {i}", "email": f"pagesup{i}@test.com"})
        resp = client.get(SUPPLIERS_URL, params={"skip": 0, "limit": 2}, headers=auth(staff_token))
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_list_excludes_deleted(self, client, staff_token):
        s = create_supplier(client, staff_token, {"name": "To Delete", "email": "del@test.com"})
        client.delete(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        resp = client.get(SUPPLIERS_URL, headers=auth(staff_token))
        ids = [s["id"] for s in resp.json()]
        assert s["id"] not in ids


# ── get single ───────────────────────────────────────────────────────────────

class TestGetSupplier:
    def test_get_supplier(self, client, staff_token):
        s = create_supplier(client, staff_token)
        resp = client.get(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == s["id"]
        assert resp.json()["email"] == s["email"]

    def test_get_supplier_not_found(self, client, staff_token):
        resp = client.get(f"{SUPPLIERS_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_get_deleted_supplier_not_found(self, client, staff_token):
        s = create_supplier(client, staff_token, {"name": "Del Get", "email": "delget@test.com"})
        client.delete(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        resp = client.get(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        assert resp.status_code == 404


# ── update ───────────────────────────────────────────────────────────────────

class TestUpdateSupplier:
    def test_update_name(self, client, staff_token):
        s = create_supplier(client, staff_token)
        resp = client.put(
            f"{SUPPLIERS_URL}/{s['id']}",
            json={"name": "Renamed Supplier"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Renamed Supplier"
        assert resp.json()["email"] == s["email"]

    def test_update_lead_time(self, client, staff_token):
        s = create_supplier(client, staff_token)
        resp = client.put(
            f"{SUPPLIERS_URL}/{s['id']}",
            json={"lead_time_days": 14},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["lead_time_days"] == 14

    def test_update_categories(self, client, staff_token):
        s = create_supplier(client, staff_token)
        resp = client.put(
            f"{SUPPLIERS_URL}/{s['id']}",
            json={"categories": ["Frozen", "Beverages"]},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert set(resp.json()["categories"]) == {"Frozen", "Beverages"}

    def test_update_not_found(self, client, staff_token):
        resp = client.put(
            f"{SUPPLIERS_URL}/99999",
            json={"name": "Ghost"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 404

    def test_update_partial_fields_unchanged(self, client, staff_token):
        s = create_supplier(client, staff_token)
        resp = client.put(
            f"{SUPPLIERS_URL}/{s['id']}",
            json={"name": "Only Name Changed"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == s["email"]
        assert body["lead_time_days"] == s["lead_time_days"]


# ── delete ───────────────────────────────────────────────────────────────────

class TestDeleteSupplier:
    def test_delete_supplier(self, client, staff_token):
        s = create_supplier(client, staff_token, {"name": "Del Supplier", "email": "delsup@test.com"})
        resp = client.delete(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        assert resp.status_code == 204

    def test_delete_not_found(self, client, staff_token):
        resp = client.delete(f"{SUPPLIERS_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_delete_is_soft(self, client, staff_token, db_session):
        from app.models import Supplier as SupplierModel
        s = create_supplier(client, staff_token, {"name": "Soft Del", "email": "softdel@test.com"})
        client.delete(f"{SUPPLIERS_URL}/{s['id']}", headers=auth(staff_token))
        row = db_session.query(SupplierModel).filter(SupplierModel.id == s["id"]).first()
        assert row is not None
        assert row.is_active is False
