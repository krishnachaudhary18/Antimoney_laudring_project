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


def test_api_report_generation():
    # Start investigation to obtain case_id
    inv_res = client.post("/api/v1/investigations", json={"alert_id": "ALERT-SCENARIO-001"})
    assert inv_res.status_code == 200
    case_id = inv_res.json()["case_id"]

    # Generate case report
    rep_res = client.post(f"/api/v1/cases/{case_id}/report")
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "report" in rep_data
    assert "executive_summary" in rep_data["report"]


def test_api_timeline_and_counterfactual_reconstruction():
    inv_res = client.post("/api/v1/investigations", json={"alert_id": "ALERT-SCENARIO-001"})
    assert inv_res.status_code == 200
    case_id = inv_res.json()["case_id"]

    # Test timeline
    tl_res = client.get(f"/api/v1/investigations/{case_id}/timeline")
    assert tl_res.status_code == 200
    tl_data = tl_res.json()
    assert "events" in tl_data

    # Test counterfactual
    cf_res = client.get(f"/api/v1/investigations/{case_id}/counterfactual")
    assert cf_res.status_code == 200
    cf_data = cf_res.json()
    assert "sensitivity" in cf_data


def test_api_invalid_alert_404():
    res = client.post("/api/v1/investigations", json={"alert_id": "ALERT-NON-EXISTENT"})
    assert res.status_code == 404
