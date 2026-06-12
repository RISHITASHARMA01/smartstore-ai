"""
Tests for POST /recommendations endpoint.
Gemini API is mocked — no real API key needed.
"""
import json
from unittest.mock import patch, MagicMock

URL = "/recommendations"

MOCK_GEMINI_RESPONSE = {
    "recommendations": [
        {
            "product_id": 1,
            "product_name": "Test Product",
            "action": "restock",
            "reason": "Stock is at reorder threshold with high daily sales velocity.",
            "priority": "high",
        }
    ],
    "summary": "1 product needs immediate attention.",
}


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _mock_gemini(json_text: str):
    """Return a mock Gemini client that responds with the given JSON string."""
    mock_response = MagicMock()
    mock_response.text = json_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


# ── authentication guard ──────────────────────────────────────────────────────

class TestRecommendationsAuth:
    def test_requires_auth(self, client):
        resp = client.post(URL, json={})
        assert resp.status_code in (401, 403)


# ── no products ───────────────────────────────────────────────────────────────

class TestRecommendationsEmpty:
    def test_empty_db_returns_empty_list(self, client, staff_token):
        with patch("app.routers.recommendations.os.getenv", return_value="fake-key"), \
             patch("app.routers.recommendations.genai.Client", return_value=_mock_gemini(json.dumps(MOCK_GEMINI_RESPONSE))):
            resp = client.post(URL, json={}, headers=auth(staff_token))
        assert resp.status_code == 200
        data = resp.json()
        # No products in DB → service returns empty list, endpoint short-circuits
        assert data["recommendations"] == []
        assert "summary" in data


# ── with products ─────────────────────────────────────────────────────────────

def _create_product(client, token, sku="REC-001", name="Rec Product", stock=5, threshold=10):
    resp = client.post(
        "/products",
        json={
            "sku": sku,
            "name": name,
            "category": "Grocery",
            "stock_qty": stock,
            "unit_price": 9.99,
            "reorder_threshold": threshold,
        },
        headers=auth(token),
    )
    assert resp.status_code == 201, resp.json()
    return resp.json()


class TestRecommendationsWithData:
    def test_returns_recommendations_structure(self, client, staff_token):
        _create_product(client, staff_token)

        with patch("app.routers.recommendations.os.getenv", return_value="fake-key"), \
             patch("app.routers.recommendations.genai.Client", return_value=_mock_gemini(json.dumps(MOCK_GEMINI_RESPONSE))):
            resp = client.post(URL, json={}, headers=auth(staff_token))

        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert "summary" in data
        assert isinstance(data["recommendations"], list)

    def test_recommendation_fields(self, client, staff_token):
        _create_product(client, staff_token, sku="REC-002", name="Another Product")

        with patch("app.routers.recommendations.os.getenv", return_value="fake-key"), \
             patch("app.routers.recommendations.genai.Client", return_value=_mock_gemini(json.dumps(MOCK_GEMINI_RESPONSE))):
            resp = client.post(URL, json={}, headers=auth(staff_token))

        recs = resp.json()["recommendations"]
        assert len(recs) >= 1
        rec = recs[0]
        assert "product_id" in rec
        assert "product_name" in rec
        assert "action" in rec
        assert "reason" in rec
        assert "priority" in rec
        assert rec["action"] in ("restock", "promote", "monitor", "clearance", "cross-sell")
        assert rec["priority"] in ("high", "medium", "low")

    def test_product_id_filter(self, client, staff_token):
        product = _create_product(client, staff_token, sku="REC-003", name="Scoped Product")

        with patch("app.routers.recommendations.os.getenv", return_value="fake-key"), \
             patch("app.routers.recommendations.genai.Client", return_value=_mock_gemini(json.dumps(MOCK_GEMINI_RESPONSE))):
            resp = client.post(URL, json={"product_id": product["id"]}, headers=auth(staff_token))

        assert resp.status_code == 200

    def test_invalid_gemini_json_returns_500(self, client, staff_token):
        _create_product(client, staff_token, sku="REC-004", name="Bad JSON Product")

        with patch("app.routers.recommendations.os.getenv", return_value="fake-key"), \
             patch("app.routers.recommendations.genai.Client", return_value=_mock_gemini("not valid json {{ }}")):
            resp = client.post(URL, json={}, headers=auth(staff_token))

        assert resp.status_code == 500

    def test_missing_api_key_returns_500(self, client, staff_token):
        with patch("app.routers.recommendations.os.getenv", return_value=None):
            resp = client.post(URL, json={}, headers=auth(staff_token))
        assert resp.status_code == 500
