"""
LaundraLens X — Behavioral Baseline Engine
Calculates historical behavioral profiles and deviation scores for accounts.

Key principle: ONLY uses transactions BEFORE the alert timestamp to prevent data leakage.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd


EPSILON = 1e-6


def _safe_std(series: pd.Series) -> float:
    return float(series.std()) if len(series) > 1 else 0.0


def compute_behavioral_baseline(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
) -> dict:
    """
    Compute historical behavioral baseline for an account.

    Args:
        account_id: Target account ID
        transactions_df: All transactions (will be filtered to pre-alert history)
        alert_timestamp: Only use transactions STRICTLY before this timestamp

    Returns:
        dict with baseline metrics and deviation score
    """
    # Strictly pre-alert history only (no leakage)
    hist = transactions_df[transactions_df["timestamp"] < alert_timestamp].copy()
    hist["timestamp"] = pd.to_datetime(hist["timestamp"])

    sent = hist[hist["sender_account_id"] == account_id]["amount"].astype(float)
    received = hist[hist["receiver_account_id"] == account_id]["amount"].astype(float)
    all_amounts = pd.concat([sent, received])

    # Guard: insufficient history
    if len(all_amounts) < 3:
        return {
            "account_id": account_id,
            "has_baseline": False,
            "baseline_message": "Insufficient transaction history for behavioral baseline.",
            "behavior_deviation_score": 0.5,  # neutral when no baseline
        }

    # Transaction timing
    all_txs = hist[
        (hist["sender_account_id"] == account_id) |
        (hist["receiver_account_id"] == account_id)
    ].copy()
    all_txs["date"] = pd.to_datetime(all_txs["timestamp"]).dt.date
    tx_per_day_series = all_txs.groupby("date").size()

    # Usual hours
    all_txs["hour"] = pd.to_datetime(all_txs["timestamp"]).dt.hour
    usual_hours = all_txs["hour"].value_counts().head(3).index.tolist()

    # Usual counterparties
    sent_to = hist[hist["sender_account_id"] == account_id]["receiver_account_id"].unique().tolist()
    received_from = hist[hist["receiver_account_id"] == account_id]["sender_account_id"].unique().tolist()

    baseline = {
        "account_id": account_id,
        "has_baseline": True,
        "history_tx_count": int(len(all_txs)),
        # Inflow stats
        "avg_inflow": float(received.mean()) if len(received) > 0 else 0.0,
        "std_inflow": _safe_std(received),
        "median_inflow": float(received.median()) if len(received) > 0 else 0.0,
        "max_inflow": float(received.max()) if len(received) > 0 else 0.0,
        # Outflow stats
        "avg_outflow": float(sent.mean()) if len(sent) > 0 else 0.0,
        "std_outflow": _safe_std(sent),
        "median_outflow": float(sent.median()) if len(sent) > 0 else 0.0,
        "max_outflow": float(sent.max()) if len(sent) > 0 else 0.0,
        # General amount stats
        "avg_transaction_amount": float(all_amounts.mean()),
        "std_transaction_amount": _safe_std(all_amounts),
        "median_transaction_amount": float(all_amounts.median()),
        # Velocity
        "avg_tx_per_day": float(tx_per_day_series.mean()),
        "std_tx_per_day": _safe_std(tx_per_day_series),
        "usual_hours": usual_hours,
        # Counterparty patterns
        "usual_sent_to_count": len(sent_to),
        "usual_received_from_count": len(received_from),
        "usual_sent_to": sent_to[:20],   # cap for storage
        # Ratio
        "historical_inflow_outflow_ratio": (
            float(received.sum()) / (float(sent.sum()) + EPSILON)
            if len(sent) > 0 and len(received) > 0 else 1.0
        ),
    }
    return baseline


def compute_current_deviation(
    account_id: str,
    current_transactions: pd.DataFrame,  # the suspicious window transactions
    baseline: dict,
) -> dict:
    """
    Compute how much the current activity deviates from historical baseline.

    Uses z-score with log1p transformation for skewed monetary distributions.

    Returns:
        dict with deviation scores per signal and composite behavior_deviation_score
    """
    if not baseline.get("has_baseline"):
        return {
            "account_id": account_id,
            "behavior_deviation_score": 0.5,
            "deviation_details": {},
            "deviation_message": "No baseline available.",
        }

    sent = current_transactions[
        current_transactions["sender_account_id"] == account_id
    ]["amount"].astype(float)
    received = current_transactions[
        current_transactions["receiver_account_id"] == account_id
    ]["amount"].astype(float)

    deviations = {}

    # 1. Outflow amount deviation (log1p for skewness)
    if len(sent) > 0:
        current_outflow = float(sent.sum())
        log_current = np.log1p(current_outflow)
        log_baseline_mean = np.log1p(baseline["avg_outflow"] * max(len(sent), 1))
        log_baseline_std = max(np.log1p(baseline["std_outflow"]), EPSILON)
        outflow_dev = abs(log_current - log_baseline_mean) / log_baseline_std
        deviations["outflow_amount_deviation"] = min(float(outflow_dev) / 5.0, 1.0)  # normalize to [0,1]
    else:
        deviations["outflow_amount_deviation"] = 0.0

    # 2. Inflow amount deviation
    if len(received) > 0:
        current_inflow = float(received.sum())
        log_current = np.log1p(current_inflow)
        log_baseline_mean = np.log1p(baseline["avg_inflow"])
        log_baseline_std = max(np.log1p(baseline["std_inflow"]), EPSILON)
        inflow_dev = abs(log_current - log_baseline_mean) / log_baseline_std
        deviations["inflow_amount_deviation"] = min(float(inflow_dev) / 5.0, 1.0)
    else:
        deviations["inflow_amount_deviation"] = 0.0

    # 3. Transaction velocity deviation
    n_current = len(current_transactions[
        (current_transactions["sender_account_id"] == account_id) |
        (current_transactions["receiver_account_id"] == account_id)
    ])
    avg_daily = baseline["avg_tx_per_day"]
    std_daily = max(baseline["std_tx_per_day"], EPSILON)
    velocity_dev = abs(n_current - avg_daily) / std_daily
    deviations["velocity_deviation"] = min(float(velocity_dev) / 5.0, 1.0)

    # 4. New counterparty ratio deviation
    hist_sent_to = set(baseline.get("usual_sent_to", []))
    current_sent_to = set(
        current_transactions[current_transactions["sender_account_id"] == account_id]["receiver_account_id"].tolist()
    )
    if current_sent_to:
        new_counterparty_ratio = len(current_sent_to - hist_sent_to) / len(current_sent_to)
    else:
        new_counterparty_ratio = 0.0
    deviations["new_counterparty_ratio"] = float(new_counterparty_ratio)

    # Composite behavior_deviation_score: weighted average
    weights = {
        "outflow_amount_deviation": 0.35,
        "inflow_amount_deviation": 0.20,
        "velocity_deviation": 0.25,
        "new_counterparty_ratio": 0.20,
    }
    score = sum(deviations[k] * w for k, w in weights.items() if k in deviations)
    score = float(np.clip(score, 0.0, 1.0))

    return {
        "account_id": account_id,
        "behavior_deviation_score": score,
        "deviation_details": deviations,
        "current_tx_count": n_current,
        "new_counterparty_ratio": new_counterparty_ratio,
    }
