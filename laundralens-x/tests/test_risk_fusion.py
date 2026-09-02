"""
Unit tests for Risk Fusion and Counterfactual Sensitivity.
"""
from src.risk.scorer import compute_risk_score, get_risk_band, compute_counterfactual


def test_risk_score_calculation():
    res = compute_risk_score(
        xgboost_score=0.95,
        isolation_score=0.90,
        autoencoder_score=0.85,
        behavior_signal=0.70,
        temporal_signal=0.80,
        flow_signal=0.90,
        graph_signal=0.60,
    )
    assert 80.0 <= res["priority_score"] <= 100.0
    assert res["risk_band"] == "CRITICAL"
    assert "Investigation Priority Score" in res["label"]


def test_risk_bands():
    assert get_risk_band(85) == "CRITICAL"
    assert get_risk_band(65) == "HIGH"
    assert get_risk_band(45) == "MEDIUM"
    assert get_risk_band(20) == "LOW"


def test_counterfactual_sensitivity():
    signals = {
        "flow": 0.9,
        "temporal": 0.8,
        "behavior": 0.7,
        "graph": 0.5,
        "xgboost": 0.95,
        "isolation_forest": 0.9,
        "autoencoder": 0.85,
    }
    sensitivity = compute_counterfactual(signals, 85.0)
    assert "baseline" in sensitivity
    assert "without_flow" in sensitivity
    # Removing a high signal should decrease priority score
    assert sensitivity["without_flow"] < sensitivity["baseline"]
