"""
Unit tests for Analyst Disposition and Decisioning API.
"""
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_record_and_get_decision():
    # First start an investigation to get a valid case_id
    inv_res = client.post("/api/v1/investigations", json={"alert_id": "ALERT-SCENARIO-001"})
    assert inv_res.status_code == 200
    case_id = inv_res.json()["case_id"]

    # Post a decision
    payload = {
        "case_id": case_id,
        "action": "FILE_SAR",
        "analyst_id": "OFFICER-TEST-99",
        "reason_code": "TYP-01: Rapid Passthrough Layering",
        "notes": "Corroborated 97% conservation ratio and high temporal velocity.",
    }
    dec_res = client.post("/api/v1/decisions", json=payload)
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["action"] == "FILE_SAR"
    assert dec_data["escalation_status"] == "SUBMITTED_TO_FIU"

    # Get decision history
    hist_res = client.get(f"/api/v1/decisions/{case_id}")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) >= 1
    assert hist_data[0]["action"] == "FILE_SAR"
    assert hist_data[0]["analyst_id"] == "OFFICER-TEST-99"
