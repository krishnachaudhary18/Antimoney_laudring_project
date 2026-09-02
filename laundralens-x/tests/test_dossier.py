"""
Unit tests for Formal SAR Dossier Generator.
"""
from src.evidence.sar_dossier import SARDossierGenerator


def test_sar_dossier_generation():
    case_data = {
        "case_id": "CASE-TEST-001",
        "account_id": "ACC-TEST-001",
        "priority_score": 85.4,
        "risk_band": "CRITICAL",
        "signals": {"flow": 0.95, "temporal": 0.88, "behavior": 0.75, "graph": 0.60},
        "model_scores": {"xgboost_score": 0.98, "isolation_score": 0.92, "autoencoder_score": 0.90},
        "findings": [{"title": "High Conservation", "severity": "CRITICAL", "category": "flow", "calculation": "ratio=0.95"}],
        "timeline": {"events": [{"time_str": "10:04", "direction": "inflow", "amount_inr_str": "Rs 10L", "counterparty": "ACC-SRC"}]},
    }

    html = SARDossierGenerator.generate_html_dossier(case_data, investigator_id="OFFICER-TEST")

    assert "<!DOCTYPE html>" in html
    assert "CASE-TEST-001" in html
    assert "ACC-TEST-001" in html
    assert "CRITICAL" in html
    assert "OFFICER-TEST" in html
    assert "SHA256:" in html
