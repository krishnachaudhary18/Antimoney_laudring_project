"""
Unit tests for FastAPI endpoints.
"""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "LaundraLens X"


def test_api_alerts():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check top alert
    top = data[0]
    assert "priority_score" in top
    assert "risk_band" in top


def test_api_start_investigation():
    payload = {"alert_id": "ALERT-SCENARIO-001"}
    res = client.post("/api/v1/investigations", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "case_id" in data
    assert "priority_score" in data
    assert data["status"] == "REPORT_READY"
