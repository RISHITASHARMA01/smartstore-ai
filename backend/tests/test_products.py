import pytest

PRODUCTS_URL = "/products"

VALID_PRODUCT = {
    "sku": "TEST-001",
    "name": "Test Product",
    "category": "Dairy",
    "stock_qty": 50,
    "unit_price": 9.99,
    "reorder_threshold": 10,
}


# ── helpers ───────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_product(client, token, overrides=None):
    payload = {**VALID_PRODUCT, **(overrides or {})}
    resp = client.post(PRODUCTS_URL, json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.json()
    return resp.json()


# ── authentication guard ──────────────────────────────────────────────────────

class TestProductsAuth:
    def test_list_requires_auth(self, client):
        assert client.get(PRODUCTS_URL).status_code in (401, 403)

    def test_get_requires_auth(self, client):
        assert client.get(f"{PRODUCTS_URL}/1").status_code in (401, 403)

    def test_create_requires_auth(self, client):
        assert client.post(PRODUCTS_URL, json=VALID_PRODUCT).status_code in (401, 403)

    def test_update_requires_auth(self, client):
        assert client.put(f"{PRODUCTS_URL}/1", json={"name": "x"}).status_code in (401, 403)

    def test_delete_requires_auth(self, client):
        assert client.delete(f"{PRODUCTS_URL}/1").status_code in (401, 403)

    def test_adjust_requires_auth(self, client):
        assert client.post(
            f"{PRODUCTS_URL}/1/adjust",
            json={"change_type": "restock", "qty": 5},
        ).status_code in (401, 403)


# ── create ────────────────────────────────────────────────────────────────────

class TestCreateProduct:
    def test_create_product(self, client, staff_token):
        resp = client.post(PRODUCTS_URL, json=VALID_PRODUCT, headers=auth(staff_token))
        assert resp.status_code == 201
        body = resp.json()
        assert body["sku"] == VALID_PRODUCT["sku"]
        assert body["name"] == VALID_PRODUCT["name"]
        assert body["category"] == VALID_PRODUCT["category"]
        assert body["stock_qty"] == VALID_PRODUCT["stock_qty"]
        assert body["unit_price"] == VALID_PRODUCT["unit_price"]
        assert body["reorder_threshold"] == VALID_PRODUCT["reorder_threshold"]
        assert body["is_active"] is True
        assert "id" in body
        assert "created_at" in body

    def test_create_duplicate_sku(self, client, staff_token):
        create_product(client, staff_token)
        resp = client.post(PRODUCTS_URL, json=VALID_PRODUCT, headers=auth(staff_token))
        assert resp.status_code == 400
        assert "sku" in resp.json()["detail"].lower()

    def test_create_missing_required_fields(self, client, staff_token):
        resp = client.post(PRODUCTS_URL, json={"sku": "X"}, headers=auth(staff_token))
        assert resp.status_code == 422

    def test_create_invalid_price(self, client, staff_token):
        resp = client.post(
            PRODUCTS_URL,
            json={**VALID_PRODUCT, "unit_price": -5},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_create_negative_stock(self, client, staff_token):
        resp = client.post(
            PRODUCTS_URL,
            json={**VALID_PRODUCT, "stock_qty": -1},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_create_with_expiry_date(self, client, staff_token):
        resp = client.post(
            PRODUCTS_URL,
            json={**VALID_PRODUCT, "sku": "EXP-001", "expiry_date": "2027-12-31T00:00:00"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 201
        assert resp.json()["expiry_date"] is not None

    def test_create_defaults_stock_and_threshold(self, client, staff_token):
        payload = {"sku": "MIN-001", "name": "Minimal", "category": "Other", "unit_price": 1.0}
        resp = client.post(PRODUCTS_URL, json=payload, headers=auth(staff_token))
        assert resp.status_code == 201
        body = resp.json()
        assert body["stock_qty"] == 0
        assert body["reorder_threshold"] == 10


# ── list ──────────────────────────────────────────────────────────────────────

class TestListProducts:
    def test_list_products(self, client, staff_token):
        create_product(client, staff_token)
        resp = client.get(PRODUCTS_URL, headers=auth(staff_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_search_by_name(self, client, staff_token):
        create_product(client, staff_token, {"sku": "SEARCH-001", "name": "Unique Mango Juice"})
        resp = client.get(PRODUCTS_URL, params={"search": "Mango"}, headers=auth(staff_token))
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert any("Mango" in n for n in names)

    def test_list_search_by_sku(self, client, staff_token):
        create_product(client, staff_token, {"sku": "SKUTEST-99"})
        resp = client.get(PRODUCTS_URL, params={"search": "SKUTEST"}, headers=auth(staff_token))
        assert resp.status_code == 200
        skus = [p["sku"] for p in resp.json()]
        assert "SKUTEST-99" in skus

    def test_list_filter_by_category(self, client, staff_token):
        create_product(client, staff_token, {"sku": "CAT-001", "category": "Grains"})
        create_product(client, staff_token, {"sku": "CAT-002", "category": "Dairy"})
        resp = client.get(PRODUCTS_URL, params={"category": "Grains"}, headers=auth(staff_token))
        assert resp.status_code == 200
        categories = {p["category"] for p in resp.json()}
        assert "Grains" in categories
        assert "Dairy" not in categories

    def test_list_filter_low_stock(self, client, staff_token):
        create_product(client, staff_token, {"sku": "LOW-001", "stock_qty": 2, "reorder_threshold": 10})
        create_product(client, staff_token, {"sku": "HIGH-001", "stock_qty": 100, "reorder_threshold": 10})
        resp = client.get(PRODUCTS_URL, params={"low_stock": True}, headers=auth(staff_token))
        assert resp.status_code == 200
        skus = [p["sku"] for p in resp.json()]
        assert "LOW-001" in skus
        assert "HIGH-001" not in skus

    def test_list_pagination(self, client, staff_token):
        for i in range(5):
            create_product(client, staff_token, {"sku": f"PAGE-{i:03d}"})
        resp = client.get(PRODUCTS_URL, params={"skip": 0, "limit": 2}, headers=auth(staff_token))
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_list_excludes_deleted_products(self, client, staff_token):
        p = create_product(client, staff_token, {"sku": "DEL-LIST-001"})
        client.delete(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        resp = client.get(PRODUCTS_URL, headers=auth(staff_token))
        ids = [p["id"] for p in resp.json()]
        assert p["id"] not in ids


# ── get single ───────────────────────────────────────────────────────────────

class TestGetProduct:
    def test_get_product(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.get(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == p["id"]
        assert resp.json()["sku"] == p["sku"]

    def test_get_product_not_found(self, client, staff_token):
        resp = client.get(f"{PRODUCTS_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_get_deleted_product_not_found(self, client, staff_token):
        p = create_product(client, staff_token, {"sku": "DEL-GET-001"})
        client.delete(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        resp = client.get(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        assert resp.status_code == 404


# ── update ───────────────────────────────────────────────────────────────────

class TestUpdateProduct:
    def test_update_product_name(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.put(
            f"{PRODUCTS_URL}/{p['id']}",
            json={"name": "Updated Name"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"
        assert resp.json()["sku"] == p["sku"]

    def test_update_product_price(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.put(
            f"{PRODUCTS_URL}/{p['id']}",
            json={"unit_price": 19.99},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["unit_price"] == 19.99

    def test_update_product_not_found(self, client, staff_token):
        resp = client.put(
            f"{PRODUCTS_URL}/99999",
            json={"name": "x"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 404

    def test_update_cannot_set_stock_qty(self, client, staff_token):
        p = create_product(client, staff_token)
        original_stock = p["stock_qty"]
        resp = client.put(
            f"{PRODUCTS_URL}/{p['id']}",
            json={"stock_qty": 9999},
            headers=auth(staff_token),
        )
        # stock_qty is removed from ProductUpdate — field should be ignored (200) or rejected (422)
        if resp.status_code == 200:
            assert resp.json()["stock_qty"] == original_stock
        else:
            assert resp.status_code == 422

    def test_update_partial_fields_unchanged(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.put(
            f"{PRODUCTS_URL}/{p['id']}",
            json={"name": "New Name Only"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["category"] == p["category"]
        assert body["unit_price"] == p["unit_price"]


# ── delete ───────────────────────────────────────────────────────────────────

class TestDeleteProduct:
    def test_delete_product(self, client, staff_token):
        p = create_product(client, staff_token, {"sku": "DEL-001"})
        resp = client.delete(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        assert resp.status_code == 204

    def test_delete_product_not_found(self, client, staff_token):
        resp = client.delete(f"{PRODUCTS_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_delete_is_soft(self, client, staff_token, db_session):
        from app.models import Product as ProductModel
        p = create_product(client, staff_token, {"sku": "SOFTDEL-001"})
        client.delete(f"{PRODUCTS_URL}/{p['id']}", headers=auth(staff_token))
        row = db_session.query(ProductModel).filter(ProductModel.id == p["id"]).first()
        assert row is not None
        assert row.is_active is False


# ── stock adjust ──────────────────────────────────────────────────────────────

class TestStockAdjust:
    def test_restock_increases_stock(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 10})
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "restock", "qty": 20},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_stock_qty"] == 30
        assert body["change_qty"] == 20
        assert body["change_type"] == "restock"

    def test_sale_decreases_stock(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 50})
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "sale", "qty": 15},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["new_stock_qty"] == 35
        assert body["change_qty"] == -15

    def test_write_off_decreases_stock(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 20})
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "write_off", "qty": 5},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["new_stock_qty"] == 15

    def test_adjustment_increases_stock(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 10})
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "adjustment", "qty": 5},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["new_stock_qty"] == 15

    def test_sale_cannot_go_below_zero(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 5})
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "sale", "qty": 10},
            headers=auth(staff_token),
        )
        assert resp.status_code == 400

    def test_adjust_invalid_change_type(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "invalid_type", "qty": 5},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_adjust_zero_qty_rejected(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "restock", "qty": 0},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_adjust_product_not_found(self, client, staff_token):
        resp = client.post(
            f"{PRODUCTS_URL}/99999/adjust",
            json={"change_type": "restock", "qty": 5},
            headers=auth(staff_token),
        )
        assert resp.status_code == 404

    def test_adjust_creates_stock_history(self, client, staff_token, db_session):
        from app.models import StockHistory
        p = create_product(client, staff_token)
        client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "restock", "qty": 25},
            headers=auth(staff_token),
        )
        history = (
            db_session.query(StockHistory)
            .filter(StockHistory.product_id == p["id"])
            .all()
        )
        assert len(history) == 1
        assert history[0].change_qty == 25
        assert history[0].change_type == "restock"


# ── stock history ─────────────────────────────────────────────────────────────

class TestStockHistory:
    def test_history_empty_on_new_product(self, client, staff_token):
        p = create_product(client, staff_token)
        resp = client.get(f"{PRODUCTS_URL}/{p['id']}/history", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_records_adjustments(self, client, staff_token):
        p = create_product(client, staff_token, {"stock_qty": 50})
        client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "sale", "qty": 10},
            headers=auth(staff_token),
        )
        client.post(
            f"{PRODUCTS_URL}/{p['id']}/adjust",
            json={"change_type": "restock", "qty": 30},
            headers=auth(staff_token),
        )
        resp = client.get(f"{PRODUCTS_URL}/{p['id']}/history", headers=auth(staff_token))
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) == 2
        types = {r["change_type"] for r in rows}
        assert types == {"sale", "restock"}

    def test_history_not_found(self, client, staff_token):
        resp = client.get(f"{PRODUCTS_URL}/99999/history", headers=auth(staff_token))
        assert resp.status_code == 404
