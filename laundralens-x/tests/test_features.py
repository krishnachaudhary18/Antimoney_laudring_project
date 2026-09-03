"""
Unit tests for Feature Intelligence Engine.
"""
from datetime import datetime, timedelta
import pandas as pd
import pytest

from src.features.behavioral import compute_behavioral_baseline, compute_current_deviation
from src.features.temporal import compute_temporal_features, compute_redistribution_timing
from src.features.flow import compute_flow_features
from src.features.network import build_transaction_graph, compute_network_features


@pytest.fixture
def sample_txs():
    base = datetime(2026, 8, 14, 10, 0, 0)
    data = [
        {"transaction_id": "T0", "timestamp": base - timedelta(days=10), "sender_account_id": "ACC-S", "receiver_account_id": "ACC-B", "amount": 50000.0},
        {"transaction_id": "T1", "timestamp": base - timedelta(days=5), "sender_account_id": "ACC-B", "receiver_account_id": "ACC-R", "amount": 30000.0},
        {"transaction_id": "T2", "timestamp": base, "sender_account_id": "ACC-A", "receiver_account_id": "ACC-B", "amount": 1000000.0},
        {"transaction_id": "T3", "timestamp": base + timedelta(minutes=20), "sender_account_id": "ACC-B", "receiver_account_id": "ACC-C", "amount": 500000.0},
        {"transaction_id": "T4", "timestamp": base + timedelta(minutes=40), "sender_account_id": "ACC-B", "receiver_account_id": "ACC-D", "amount": 470000.0},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def test_behavioral_baseline(sample_txs):
    alert_time = datetime(2026, 8, 14, 10, 0, 0)
    baseline = compute_behavioral_baseline("ACC-B", sample_txs, alert_time)
    assert baseline["has_baseline"] is False or baseline["history_tx_count"] == 2


def test_flow_features(sample_txs):
    alert_time = datetime(2026, 8, 14, 11, 0, 0)
    flow = compute_flow_features("ACC-B", sample_txs, alert_time)
    assert flow["inflow_total_24h"] == 1000000.0
    assert flow["outflow_total_24h"] == 970000.0
    assert flow["conservation_ratio"] == pytest.approx(0.97, 0.01)
    assert flow["flow_signal"] > 0.6


def test_redistribution_timing(sample_txs):
    alert_time = datetime(2026, 8, 14, 11, 0, 0)
    timing = compute_redistribution_timing("ACC-B", sample_txs, alert_time)
    assert timing["time_to_first_outflow_minutes"] == pytest.approx(20.0, 1.0)
    assert timing["time_to_90pct_outflow_minutes"] == pytest.approx(40.0, 1.0)
    assert timing["redistribution_speed_score"] > 0.8


def test_network_features(sample_txs):
    G = build_transaction_graph(sample_txs)
    assert G.number_of_nodes() >= 5
    features = compute_network_features("ACC-B", G)
    assert features["in_graph"] is True
    assert features["out_degree"] >= 2


def test_flow_features_zero_inflow(sample_txs):
    """Verify that an account with 0 inflow and positive outflow does not produce division-by-zero overflow."""
    alert_time = datetime(2026, 8, 14, 11, 0, 0)
    # ACC-A only has outgoing in the window
    flow = compute_flow_features("ACC-A", sample_txs, alert_time)
    assert flow["inflow_total_24h"] == 0.0
    assert flow["outflow_total_24h"] == 1000000.0
    assert flow["conservation_ratio"] == 0.0  # Must not be 1e12!
    assert 0.0 <= flow["flow_signal"] <= 1.0


def test_flow_features_zero_transactions():
    """Verify empty transactions return clean zero signals."""
    alert_time = datetime(2026, 8, 14, 11, 0, 0)
    empty_df = pd.DataFrame(columns=["transaction_id", "timestamp", "sender_account_id", "receiver_account_id", "amount"])
    flow = compute_flow_features("ACC-EMPTY", empty_df, alert_time)
    assert flow["conservation_ratio"] == 0.0
    assert flow["flow_signal"] == 0.0
