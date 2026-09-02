"""
LaundraLens X — Temporal Feature Engine
Multi-window transaction analysis with rapid-redistribution detection signals.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np
import pandas as pd


WINDOWS = {
    "15m": timedelta(minutes=15),
    "1h": timedelta(hours=1),
    "6h": timedelta(hours=6),
    "24h": timedelta(hours=24),
    "3d": timedelta(days=3),
    "7d": timedelta(days=7),
}

EPSILON = 1e-6


def compute_window_features(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
    window_name: str,
) -> dict:
    """Compute features for a single time window."""
    window_delta = WINDOWS[window_name]
    window_start = alert_timestamp - window_delta

    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    window_txs = df[
        (df["timestamp"] >= window_start) &
        (df["timestamp"] <= alert_timestamp)
    ]

    inflows = window_txs[window_txs["receiver_account_id"] == account_id]
    outflows = window_txs[window_txs["sender_account_id"] == account_id]

    inflow_total = float(inflows["amount"].sum())
    outflow_total = float(outflows["amount"].sum())
    tx_count = len(window_txs[
        (window_txs["sender_account_id"] == account_id) |
        (window_txs["receiver_account_id"] == account_id)
    ])

    # Unique counterparties
    sent_to = set(outflows["receiver_account_id"].tolist())
    recv_from = set(inflows["sender_account_id"].tolist())
    all_counterparties = sent_to | recv_from

    # Velocity
    duration_hours = window_delta.total_seconds() / 3600
    transaction_velocity = tx_count / (duration_hours + EPSILON)  # tx per hour
    amount_velocity = (inflow_total + outflow_total) / (duration_hours + EPSILON)

    return {
        f"{window_name}_inflow_total": inflow_total,
        f"{window_name}_outflow_total": outflow_total,
        f"{window_name}_tx_count": tx_count,
        f"{window_name}_incoming_count": len(inflows),
        f"{window_name}_outgoing_count": len(outflows),
        f"{window_name}_unique_counterparties": len(all_counterparties),
        f"{window_name}_transaction_velocity": round(transaction_velocity, 4),
        f"{window_name}_amount_velocity": round(amount_velocity, 2),
    }


def compute_redistribution_timing(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
    window_hours: int = 24,
) -> dict:
    """
    Compute rapid-redistribution timing signals.
    Measures how quickly incoming funds flow back out.

    Returns time_to_first_outflow, time_to_50pct_outflow, time_to_90pct_outflow.
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    window_start = alert_timestamp - timedelta(hours=window_hours)

    window_txs = df[
        (df["timestamp"] >= window_start) &
        (df["timestamp"] <= alert_timestamp)
    ].sort_values("timestamp")

    inflows = window_txs[window_txs["receiver_account_id"] == account_id]
    outflows = window_txs[window_txs["sender_account_id"] == account_id]

    if inflows.empty or outflows.empty:
        return {
            "time_to_first_outflow_minutes": None,
            "time_to_50pct_outflow_minutes": None,
            "time_to_90pct_outflow_minutes": None,
            "redistribution_speed_score": 0.0,
        }

    # First inflow timestamp
    first_inflow_ts = inflows["timestamp"].min()
    total_inflow = float(inflows["amount"].sum())
    total_outflow = float(outflows["amount"].sum())

    if total_inflow == 0:
        return {
            "time_to_first_outflow_minutes": None,
            "time_to_50pct_outflow_minutes": None,
            "time_to_90pct_outflow_minutes": None,
            "redistribution_speed_score": 0.0,
        }

    # Time to first outflow after first inflow
    post_inflow_outflows = outflows[outflows["timestamp"] >= first_inflow_ts].copy()
    if post_inflow_outflows.empty:
        return {
            "time_to_first_outflow_minutes": None,
            "time_to_50pct_outflow_minutes": None,
            "time_to_90pct_outflow_minutes": None,
            "redistribution_speed_score": 0.0,
        }

    time_to_first = (
        post_inflow_outflows["timestamp"].min() - first_inflow_ts
    ).total_seconds() / 60

    # Cumulative outflow — time to 50% and 90%
    post_inflow_outflows = post_inflow_outflows.sort_values("timestamp")
    post_inflow_outflows["cumulative_out"] = post_inflow_outflows["amount"].cumsum()

    target_50 = total_inflow * 0.50
    target_90 = total_inflow * 0.90

    time_to_50 = None
    time_to_90 = None

    for _, row in post_inflow_outflows.iterrows():
        minutes = (row["timestamp"] - first_inflow_ts).total_seconds() / 60
        if time_to_50 is None and row["cumulative_out"] >= target_50:
            time_to_50 = minutes
        if time_to_90 is None and row["cumulative_out"] >= target_90:
            time_to_90 = minutes
            break

    # Speed score: higher = faster redistribution = more suspicious
    # Normalize: 0 minutes → 1.0, 7 days → 0.0
    max_minutes = 7 * 24 * 60
    if time_to_90 is not None:
        speed_score = 1.0 - min(time_to_90 / max_minutes, 1.0)
    elif time_to_50 is not None:
        speed_score = 0.7 * (1.0 - min(time_to_50 / max_minutes, 1.0))
    else:
        speed_score = 0.3 * (1.0 - min(time_to_first / max_minutes, 1.0)) if time_to_first else 0.0

    return {
        "time_to_first_outflow_minutes": round(time_to_first, 1) if time_to_first is not None else None,
        "time_to_50pct_outflow_minutes": round(time_to_50, 1) if time_to_50 is not None else None,
        "time_to_90pct_outflow_minutes": round(time_to_90, 1) if time_to_90 is not None else None,
        "redistribution_speed_score": round(float(speed_score), 4),
    }


def compute_temporal_features(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
) -> dict:
    """
    Compute all temporal features across all time windows.
    Also computes redistribution timing signals.

    Returns complete temporal feature dict.
    """
    features: dict = {"account_id": account_id}

    # Per-window features
    for window_name in WINDOWS:
        wf = compute_window_features(account_id, transactions_df, alert_timestamp, window_name)
        features.update(wf)

    # Redistribution timing (24h window)
    timing = compute_redistribution_timing(account_id, transactions_df, alert_timestamp, window_hours=24)
    features.update(timing)

    # Composite temporal_signal [0,1]
    # Combines: redistribution speed + velocity (1h) + new counterparty activity (6h)
    vel_1h = features.get("1h_transaction_velocity", 0.0)
    speed = features.get("redistribution_speed_score", 0.0)
    outgoing_1h = features.get("1h_outgoing_count", 0)
    incoming_1h = features.get("1h_incoming_count", 0)

    # Velocity signal — normalize 10+ tx/hr as max
    vel_signal = min(vel_1h / 10.0, 1.0)

    # Burst signal — did outgoing spike relative to incoming?
    burst_signal = min(outgoing_1h / (incoming_1h + EPSILON), 1.0) if incoming_1h > 0 else 0.0

    temporal_signal = float(np.clip(
        0.50 * speed + 0.30 * vel_signal + 0.20 * burst_signal,
        0.0, 1.0
    ))
    features["temporal_signal"] = round(temporal_signal, 4)

    return features
