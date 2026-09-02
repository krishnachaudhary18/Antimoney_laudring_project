"""
LaundraLens X — Flow Analysis Engine
Computes fund flow signals: conservation ratio, redistribution metrics, recipient analysis.

Key signal: conservation_ratio = outflow / (inflow + ε)
A ratio close to 1.0 means almost all inflow was sent onward — potential layering.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

EPSILON = 1e-6


def compute_flow_features(
    account_id: str,
    transactions_df: pd.DataFrame,
    alert_timestamp: datetime,
    primary_window_hours: int = 24,
    history_days: int = 30,
) -> dict:
    """
    Compute all fund flow signals for an account.

    Args:
        account_id: Target account
        transactions_df: All transactions (historical + current)
        alert_timestamp: Alert trigger time
        primary_window_hours: Main window for conservation ratio
        history_days: Historical period for counterparty baseline

    Returns:
        dict with flow features and flow_signal [0,1]
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # --- Primary window (conservation analysis) ---
    window_start = alert_timestamp - timedelta(hours=primary_window_hours)
    current = df[
        (df["timestamp"] >= window_start) &
        (df["timestamp"] <= alert_timestamp)
    ]

    inflows = current[current["receiver_account_id"] == account_id]
    outflows = current[current["sender_account_id"] == account_id]

    inflow_total = float(inflows["amount"].sum())
    outflow_total = float(outflows["amount"].sum())
    net_flow = inflow_total - outflow_total

    # Conservation ratio (primary signal)
    conservation_ratio = outflow_total / (inflow_total + EPSILON)

    # Redistribution ratio: how much of inflow was immediately redistributed
    redistribution_ratio = min(conservation_ratio, 1.0)

    # --- Recipient analysis ---
    # Historical counterparties (before alert window)
    hist_start = alert_timestamp - timedelta(days=history_days)
    historical = df[
        (df["timestamp"] >= hist_start) &
        (df["timestamp"] < window_start)
    ]
    hist_recipients = set(
        historical[historical["sender_account_id"] == account_id]["receiver_account_id"].tolist()
    )

    # Current recipients
    current_recipients = set(outflows["receiver_account_id"].tolist())
    new_recipients = current_recipients - hist_recipients
    new_recipient_count = len(new_recipients)
    total_recipient_count = len(current_recipients)
    new_recipient_ratio = (
        new_recipient_count / total_recipient_count
        if total_recipient_count > 0 else 0.0
    )

    # Recipient concentration (HHI-based: 1.0 = all to one, 0.0 = perfectly spread)
    if total_recipient_count > 0 and outflow_total > 0:
        recipient_shares = [
            float(outflows[outflows["receiver_account_id"] == r]["amount"].sum()) / outflow_total
            for r in current_recipients
        ]
        concentration = float(np.sum(np.square(recipient_shares)))
    else:
        concentration = 0.0

    # Amount concentration (what fraction goes to largest single recipient)
    if total_recipient_count > 0 and outflow_total > 0:
        per_recipient = {
            r: float(outflows[outflows["receiver_account_id"] == r]["amount"].sum())
            for r in current_recipients
        }
        amount_concentration = max(per_recipient.values()) / outflow_total if per_recipient else 0.0
    else:
        amount_concentration = 0.0

    # --- Downstream movement (recipients who then send money out) ---
    # Check if any current recipients made outgoing transactions after receiving
    downstream_count = 0
    downstream_amount = 0.0
    if not outflows.empty and not df.empty:
        for rcv_id in current_recipients:
            # Find outflows from this recipient after they received from account_id
            receipt_time = df[
                (df["receiver_account_id"] == rcv_id) &
                (df["sender_account_id"] == account_id)
            ]["timestamp"].min()

            if pd.isnull(receipt_time):
                continue

            downstream_txs = df[
                (df["sender_account_id"] == rcv_id) &
                (df["timestamp"] > receipt_time)
            ]
            if not downstream_txs.empty:
                downstream_count += 1
                downstream_amount += float(downstream_txs["amount"].sum())

    onward_movement = downstream_count > 0

    # --- Flow Signal [0,1] ---
    # High conservation ratio + new recipients + fast redistribution = high flow signal
    conservation_signal = min(conservation_ratio, 1.0)
    new_recipient_signal = float(new_recipient_ratio)
    downstream_signal = min(downstream_amount / (inflow_total + EPSILON), 1.0)

    flow_signal = float(np.clip(
        0.45 * conservation_signal +
        0.35 * new_recipient_signal +
        0.20 * downstream_signal,
        0.0, 1.0
    ))

    return {
        "account_id": account_id,
        # Primary signals
        "conservation_ratio": round(conservation_ratio, 4),
        "redistribution_ratio": round(redistribution_ratio, 4),
        "inflow_outflow_ratio": round(inflow_total / (outflow_total + EPSILON), 4),
        # Volume
        "inflow_total_24h": round(inflow_total, 2),
        "outflow_total_24h": round(outflow_total, 2),
        "net_flow_24h": round(net_flow, 2),
        # Recipient analysis
        "recipient_count": total_recipient_count,
        "new_recipient_count": new_recipient_count,
        "new_recipient_ratio": round(new_recipient_ratio, 4),
        "recipient_concentration": round(concentration, 4),
        "amount_concentration": round(amount_concentration, 4),
        # Downstream
        "onward_movement": onward_movement,
        "downstream_recipient_count": downstream_count,
        "downstream_amount": round(downstream_amount, 2),
        # Composite
        "flow_signal": round(flow_signal, 4),
    }
