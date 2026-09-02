"""
LaundraLens X — Feature Pipeline
Orchestrates all 4 feature modules into a unified feature vector per account.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

import pandas as pd
import networkx as nx

from src.features.behavioral import compute_behavioral_baseline, compute_current_deviation
from src.features.temporal import compute_temporal_features
from src.features.flow import compute_flow_features
from src.features.network import compute_network_features, build_transaction_graph


def compute_features(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
    graph: Optional[nx.DiGraph] = None,
    suspicious_account_ids: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Compute the complete feature vector for an account at alert time.

    Args:
        account_id: Target account
        transactions_df: All transactions (historical + current)
        alert_timestamp: Point in time of the alert
        graph: Pre-built NetworkX graph (optional, built if not provided)
        suspicious_account_ids: Known suspicious accounts for graph features

    Returns:
        Unified feature dict with all signals and composite scores
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- 1. Behavioral features ---
    baseline = compute_behavioral_baseline(account_id, df, alert_timestamp)
    # Current window = last 24h (the suspicious period)
    from datetime import timedelta
    window_start = alert_timestamp - timedelta(hours=24)
    current_txs = df[
        (df["timestamp"] >= window_start) &
        (df["timestamp"] <= alert_timestamp)
    ]
    deviation = compute_current_deviation(account_id, current_txs, baseline)

    # --- 2. Temporal features ---
    temporal = compute_temporal_features(account_id, df, alert_timestamp)

    # --- 3. Flow features ---
    flow = compute_flow_features(account_id, df, alert_timestamp)

    # --- 4. Network features ---
    if graph is None:
        graph = build_transaction_graph(df, alert_timestamp=alert_timestamp)
    network = compute_network_features(account_id, graph, suspicious_account_ids)

    # --- Merge all features ---
    features: Dict[str, Any] = {
        "account_id": account_id,
        "alert_timestamp": alert_timestamp.isoformat(),
    }
    features.update({k: v for k, v in baseline.items() if k != "account_id"})
    features.update({k: v for k, v in deviation.items() if k != "account_id"})
    features.update({k: v for k, v in temporal.items() if k != "account_id"})
    features.update({k: v for k, v in flow.items() if k != "account_id"})
    features.update({k: v for k, v in network.items() if k != "account_id"})

    return features


def features_to_ml_vector(features: Dict[str, Any]) -> list:
    """
    Extract numeric ML features in a consistent order for model input.
    Only includes features that are reliably numeric and non-None.
    """
    ML_FEATURE_NAMES = [
        # Behavioral
        "behavior_deviation_score",
        "outflow_amount_deviation",
        "inflow_amount_deviation",
        "velocity_deviation",
        "new_counterparty_ratio",
        # Temporal
        "1h_inflow_total",
        "1h_outflow_total",
        "1h_tx_count",
        "1h_outgoing_count",
        "1h_transaction_velocity",
        "24h_inflow_total",
        "24h_outflow_total",
        "24h_tx_count",
        "24h_outgoing_count",
        "24h_transaction_velocity",
        "redistribution_speed_score",
        "temporal_signal",
        # Flow
        "conservation_ratio",
        "redistribution_ratio",
        "inflow_total_24h",
        "outflow_total_24h",
        "recipient_count",
        "new_recipient_count",
        "new_recipient_ratio",
        "recipient_concentration",
        "amount_concentration",
        "downstream_recipient_count",
        "flow_signal",
        # Network
        "in_degree",
        "out_degree",
        "weighted_in_degree",
        "weighted_out_degree",
        "fan_in",
        "fan_out",
        "counterparty_count",
        "degree_centrality",
        "betweenness_centrality",
        "k_hop_network_size",
        "graph_signal",
    ]

    vector = []
    for name in ML_FEATURE_NAMES:
        val = features.get(name)
        if val is None or (isinstance(val, float) and (val != val)):  # NaN check
            val = 0.0
        vector.append(float(val))

    return vector


ML_FEATURE_NAMES = [
    "behavior_deviation_score", "outflow_amount_deviation", "inflow_amount_deviation",
    "velocity_deviation", "new_counterparty_ratio",
    "1h_inflow_total", "1h_outflow_total", "1h_tx_count", "1h_outgoing_count", "1h_transaction_velocity",
    "24h_inflow_total", "24h_outflow_total", "24h_tx_count", "24h_outgoing_count", "24h_transaction_velocity",
    "redistribution_speed_score", "temporal_signal",
    "conservation_ratio", "redistribution_ratio", "inflow_total_24h", "outflow_total_24h",
    "recipient_count", "new_recipient_count", "new_recipient_ratio",
    "recipient_concentration", "amount_concentration", "downstream_recipient_count", "flow_signal",
    "in_degree", "out_degree", "weighted_in_degree", "weighted_out_degree",
    "fan_in", "fan_out", "counterparty_count", "degree_centrality", "betweenness_centrality",
    "k_hop_network_size", "graph_signal",
]
