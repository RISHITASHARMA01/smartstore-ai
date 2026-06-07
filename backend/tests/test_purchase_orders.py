import pytest

PO_URL = "/purchase-orders"

VALID_SUPPLIER = {
    "name": "PO Test Supplier",
    "email": "posupplier@test.com",
    "categories": ["Dairy"],
    "lead_time_days": 5,
}

VALID_PRODUCT = {
    "sku": "PO-PROD-001",
    "name": "PO Test Product",
    "category": "Dairy",
    "stock_qty": 100,
    "unit_price": 5.00,
}


# ── helpers ───────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


def create_supplier(client, token, overrides=None):
    payload = {**VALID_SUPPLIER, **(overrides or {})}
    resp = client.post("/suppliers", json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.json()
    return resp.json()


def create_product(client, token, overrides=None):
    payload = {**VALID_PRODUCT, **(overrides or {})}
    resp = client.post("/products", json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.json()
    return resp.json()


def create_po(client, token, supplier_id, product_id, overrides=None):
    payload = {
        "supplier_id": supplier_id,
        "line_items": [{"product_id": product_id, "quantity": 10, "unit_price": 5.00}],
        **(overrides or {}),
    }
    resp = client.post(PO_URL, json=payload, headers=auth(token))
    assert resp.status_code == 201, resp.json()
    return resp.json()


def advance(client, token, po_id):
    resp = client.patch(f"{PO_URL}/{po_id}/status", headers=auth(token))
    assert resp.status_code == 200, resp.json()
    return resp.json()


@pytest.fixture()
def supplier(client, staff_token):
    return create_supplier(client, staff_token)


@pytest.fixture()
def product(client, staff_token):
    return create_product(client, staff_token)


@pytest.fixture()
def po(client, staff_token, supplier, product):
    return create_po(client, staff_token, supplier["id"], product["id"])


# ── authentication guard ──────────────────────────────────────────────────────

class TestPOAuth:
    def test_list_requires_auth(self, client):
        assert client.get(PO_URL).status_code in (401, 403)

    def test_get_requires_auth(self, client):
        assert client.get(f"{PO_URL}/1").status_code in (401, 403)

    def test_create_requires_auth(self, client):
        assert client.post(PO_URL, json={}).status_code in (401, 403)

    def test_advance_requires_auth(self, client):
        assert client.patch(f"{PO_URL}/1/status").status_code in (401, 403)

    def test_delete_requires_auth(self, client):
        assert client.delete(f"{PO_URL}/1").status_code in (401, 403)


# ── create ────────────────────────────────────────────────────────────────────

class TestCreatePO:
    def test_create_po(self, client, staff_token, supplier, product):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "line_items": [
                    {"product_id": product["id"], "quantity": 10, "unit_price": 5.00}
                ],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["supplier_id"] == supplier["id"]
        assert body["status"] == "Draft"
        assert len(body["line_items"]) == 1
        assert body["total_value"] == 50.0
        assert body["line_items"][0]["product"]["id"] == product["id"]

    def test_create_po_multiple_line_items(self, client, staff_token, supplier):
        p1 = create_product(client, staff_token, {"sku": "MULTI-01", "unit_price": 4.0})
        p2 = create_product(client, staff_token, {"sku": "MULTI-02", "unit_price": 6.0})
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "line_items": [
                    {"product_id": p1["id"], "quantity": 5, "unit_price": 4.0},
                    {"product_id": p2["id"], "quantity": 5, "unit_price": 6.0},
                ],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert len(body["line_items"]) == 2
        assert body["total_value"] == 50.0

    def test_create_po_calculates_total(self, client, staff_token, supplier, product):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "line_items": [{"product_id": product["id"], "quantity": 7, "unit_price": 3.50}],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 201
        assert resp.json()["total_value"] == pytest.approx(24.50)

    def test_create_po_with_notes(self, client, staff_token, supplier, product):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "notes": "Urgent delivery needed",
                "line_items": [{"product_id": product["id"], "quantity": 1, "unit_price": 5.0}],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 201
        assert resp.json()["notes"] == "Urgent delivery needed"

    def test_create_po_invalid_supplier(self, client, staff_token, product):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": 99999,
                "line_items": [{"product_id": product["id"], "quantity": 1, "unit_price": 5.0}],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 404
        assert "supplier" in resp.json()["detail"].lower()

    def test_create_po_invalid_product(self, client, staff_token, supplier):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "line_items": [{"product_id": 99999, "quantity": 1, "unit_price": 5.0}],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 404
        assert "product" in resp.json()["detail"].lower()

    def test_create_po_empty_line_items_rejected(self, client, staff_token, supplier):
        resp = client.post(
            PO_URL,
            json={"supplier_id": supplier["id"], "line_items": []},
            headers=auth(staff_token),
        )
        assert resp.status_code == 422

    def test_create_po_zero_quantity_rejected(self, client, staff_token, supplier, product):
        resp = client.post(
            PO_URL,
            json={
                "supplier_id": supplier["id"],
                "line_items": [{"product_id": product["id"], "quantity": 0, "unit_price": 5.0}],
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 422


# ── list ──────────────────────────────────────────────────────────────────────

class TestListPOs:
    def test_list_purchase_orders(self, client, staff_token, po):
        resp = client.get(PO_URL, headers=auth(staff_token))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        ids = [p["id"] for p in resp.json()]
        assert po["id"] in ids

    def test_list_filter_by_status(self, client, staff_token, po):
        resp = client.get(PO_URL, params={"status": "Draft"}, headers=auth(staff_token))
        assert resp.status_code == 200
        statuses = {p["status"] for p in resp.json()}
        assert statuses == {"Draft"}

    def test_list_filter_by_supplier(self, client, staff_token, supplier, product):
        other_supplier = create_supplier(client, staff_token, {"name": "Other Sup", "email": "other@test.com"})
        po1 = create_po(client, staff_token, supplier["id"], product["id"])
        po2 = create_po(client, staff_token, other_supplier["id"], product["id"])

        resp = client.get(PO_URL, params={"supplier_id": supplier["id"]}, headers=auth(staff_token))
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert po1["id"] in ids
        assert po2["id"] not in ids

    def test_list_pagination(self, client, staff_token, supplier, product):
        for _ in range(3):
            create_po(client, staff_token, supplier["id"], product["id"])
        resp = client.get(PO_URL, params={"skip": 0, "limit": 2}, headers=auth(staff_token))
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    def test_list_includes_line_items(self, client, staff_token, po):
        resp = client.get(PO_URL, headers=auth(staff_token))
        assert resp.status_code == 200
        match = next((p for p in resp.json() if p["id"] == po["id"]), None)
        assert match is not None
        assert len(match["line_items"]) > 0


# ── get single ───────────────────────────────────────────────────────────────

class TestGetPO:
    def test_get_po(self, client, staff_token, po):
        resp = client.get(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == po["id"]
        assert body["status"] == "Draft"
        assert "supplier" in body
        assert "line_items" in body

    def test_get_po_not_found(self, client, staff_token):
        resp = client.get(f"{PO_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404


# ── update ───────────────────────────────────────────────────────────────────

class TestUpdatePO:
    def test_update_notes(self, client, staff_token, po):
        resp = client.put(
            f"{PO_URL}/{po['id']}",
            json={"notes": "Updated note"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated note"

    def test_update_line_items_replaces_all(self, client, staff_token, supplier, product):
        p2 = create_product(client, staff_token, {"sku": "REPLACE-01", "unit_price": 8.0})
        po = create_po(client, staff_token, supplier["id"], product["id"])
        resp = client.put(
            f"{PO_URL}/{po['id']}",
            json={
                "line_items": [{"product_id": p2["id"], "quantity": 3, "unit_price": 8.0}]
            },
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["line_items"]) == 1
        assert body["line_items"][0]["product"]["id"] == p2["id"]
        assert body["total_value"] == pytest.approx(24.0)

    def test_update_recalculates_total(self, client, staff_token, supplier, product):
        po = create_po(client, staff_token, supplier["id"], product["id"])
        resp = client.put(
            f"{PO_URL}/{po['id']}",
            json={"line_items": [{"product_id": product["id"], "quantity": 20, "unit_price": 5.0}]},
            headers=auth(staff_token),
        )
        assert resp.status_code == 200
        assert resp.json()["total_value"] == pytest.approx(100.0)

    def test_update_not_draft_rejected(self, client, staff_token, po):
        advance(client, staff_token, po["id"])  # Draft → Sent
        resp = client.put(
            f"{PO_URL}/{po['id']}",
            json={"notes": "Should fail"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower()

    def test_update_not_found(self, client, staff_token):
        resp = client.put(
            f"{PO_URL}/99999",
            json={"notes": "Ghost"},
            headers=auth(staff_token),
        )
        assert resp.status_code == 404


# ── status workflow ───────────────────────────────────────────────────────────

class TestPOStatusWorkflow:
    def test_advance_draft_to_sent(self, client, staff_token, po):
        resp = client.patch(f"{PO_URL}/{po['id']}/status", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "Sent"

    def test_advance_sent_to_acknowledged(self, client, staff_token, po):
        advance(client, staff_token, po["id"])  # → Sent
        resp = client.patch(f"{PO_URL}/{po['id']}/status", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "Acknowledged"

    def test_advance_acknowledged_to_received(self, client, staff_token, po):
        advance(client, staff_token, po["id"])  # → Sent
        advance(client, staff_token, po["id"])  # → Acknowledged
        resp = client.patch(f"{PO_URL}/{po['id']}/status", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "Received"

    def test_cannot_advance_past_received(self, client, staff_token, po):
        advance(client, staff_token, po["id"])  # → Sent
        advance(client, staff_token, po["id"])  # → Acknowledged
        advance(client, staff_token, po["id"])  # → Received
        resp = client.patch(f"{PO_URL}/{po['id']}/status", headers=auth(staff_token))
        assert resp.status_code == 400
        assert "received" in resp.json()["detail"].lower()

    def test_advance_not_found(self, client, staff_token):
        resp = client.patch(f"{PO_URL}/99999/status", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_receipt_increases_stock(self, client, staff_token, supplier):
        product = create_product(client, staff_token, {"sku": "STOCK-REC-01", "stock_qty": 10})
        po = create_po(
            client, staff_token, supplier["id"], product["id"],
            {"line_items": [{"product_id": product["id"], "quantity": 25, "unit_price": 5.0}]},
        )
        advance(client, staff_token, po["id"])  # → Sent
        advance(client, staff_token, po["id"])  # → Acknowledged
        advance(client, staff_token, po["id"])  # → Received

        resp = client.get(f"/products/{product['id']}", headers=auth(staff_token))
        assert resp.status_code == 200
        assert resp.json()["stock_qty"] == 35  # 10 + 25

    def test_receipt_creates_stock_history(self, client, staff_token, supplier, db_session):
        from app.models import StockHistory
        product = create_product(client, staff_token, {"sku": "HIST-REC-01", "stock_qty": 0})
        po = create_po(
            client, staff_token, supplier["id"], product["id"],
            {"line_items": [{"product_id": product["id"], "quantity": 15, "unit_price": 5.0}]},
        )
        advance(client, staff_token, po["id"])  # → Sent
        advance(client, staff_token, po["id"])  # → Acknowledged
        advance(client, staff_token, po["id"])  # → Received

        history = (
            db_session.query(StockHistory)
            .filter(StockHistory.product_id == product["id"])
            .all()
        )
        assert len(history) == 1
        assert history[0].change_qty == 15
        assert history[0].change_type == "restock"


# ── delete ───────────────────────────────────────────────────────────────────

class TestDeletePO:
    def test_delete_draft_po(self, client, staff_token, supplier, product):
        po = create_po(client, staff_token, supplier["id"], product["id"])
        resp = client.delete(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        assert resp.status_code == 204

    def test_deleted_po_not_found(self, client, staff_token, supplier, product):
        po = create_po(client, staff_token, supplier["id"], product["id"])
        client.delete(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        resp = client.get(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_delete_non_draft_rejected(self, client, staff_token, po):
        advance(client, staff_token, po["id"])  # → Sent
        resp = client.delete(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower()

    def test_delete_not_found(self, client, staff_token):
        resp = client.delete(f"{PO_URL}/99999", headers=auth(staff_token))
        assert resp.status_code == 404

    def test_delete_removes_line_items(self, client, staff_token, supplier, product, db_session):
        from app.models import POLineItem
        po = create_po(client, staff_token, supplier["id"], product["id"])
        client.delete(f"{PO_URL}/{po['id']}", headers=auth(staff_token))
        remaining = db_session.query(POLineItem).filter(POLineItem.po_id == po["id"]).count()
        assert remaining == 0
