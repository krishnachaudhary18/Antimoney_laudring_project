"""
LaundraLens X — Potential Fund Lineage Engine
Heuristic engine tracing candidate downstream movement.

IMPORTANT: Always uses labels like "potential_downstream_lineage".
Never uses "confirmed_source_of_funds" or equivalent.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np


EPSILON = 1e-6


def trace_potential_lineage(
    origin_transaction_id: str,
    transactions_df: pd.DataFrame,
    max_depth: int = 4,
    time_proximity_hours: int = 48,
    amount_ratio_threshold: float = 0.3,
) -> Dict:
    """
    Heuristic lineage tracer: follows potential downstream fund movement.

    Algorithm:
    1. Find the origin transaction
    2. From receiver, find outgoing transactions within time_proximity_hours
    3. If outgoing amount >= amount_ratio_threshold * received amount → candidate hop
    4. Repeat up to max_depth hops
    5. Compute lineage_strength from temporal proximity + amount relationship

    Labels used: potential_downstream_lineage (never "confirmed")
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Find origin
    origin = df[df["transaction_id"] == origin_transaction_id]
    if origin.empty:
        return {
            "origin_transaction": origin_transaction_id,
            "candidate_downstream_transactions": [],
            "depth": 0,
            "lineage_strength": 0.0,
            "reason": "Origin transaction not found.",
            "lineage_type": "potential_downstream_lineage",
        }

    origin_row = origin.iloc[0]
    origin_amount = float(origin_row["amount"])
    origin_ts = pd.Timestamp(origin_row["timestamp"])
    origin_receiver = origin_row["receiver_account_id"]

    # BFS-style traversal
    visited_txs = {origin_transaction_id}
    visited_accounts = {origin_row["sender_account_id"]}
    frontier = [(origin_receiver, origin_amount, origin_ts, 1)]
    candidate_txs = []
    hop_scores = []

    while frontier and len(candidate_txs) < 20:
        account_id, received_amount, received_ts, depth = frontier.pop(0)

        if depth > max_depth:
            break

        visited_accounts.add(account_id)

        # Window: look for outflows from this account within time_proximity_hours
        window_end = received_ts + timedelta(hours=time_proximity_hours)
        outflows = df[
            (df["sender_account_id"] == account_id) &
            (df["timestamp"] > received_ts) &
            (df["timestamp"] <= window_end) &
            (~df["transaction_id"].isin(visited_txs))
        ].sort_values("timestamp")

        for _, outflow_row in outflows.iterrows():
            out_amount = float(outflow_row["amount"])
            out_ts = pd.Timestamp(outflow_row["timestamp"])
            tx_id = outflow_row["transaction_id"]

            # Amount relationship check
            if out_amount < received_amount * amount_ratio_threshold:
                continue

            # Temporal proximity score (closer = stronger)
            time_delta_hours = (out_ts - received_ts).total_seconds() / 3600
            temporal_score = max(0.0, 1.0 - (time_delta_hours / time_proximity_hours))

            # Amount score (proportion of received that was forwarded)
            amount_score = min(out_amount / (received_amount + EPSILON), 1.0)

            # Hop penalty (deeper hops = weaker signal)
            hop_penalty = 1.0 / depth

            hop_strength = temporal_score * amount_score * hop_penalty
            hop_scores.append(hop_strength)

            candidate_txs.append({
                "transaction_id": tx_id,
                "from_account": account_id,
                "to_account": outflow_row["receiver_account_id"],
                "amount": round(out_amount, 2),
                "timestamp": str(out_ts),
                "depth": depth,
                "temporal_proximity_hours": round(time_delta_hours, 1),
                "amount_ratio": round(out_amount / (received_amount + EPSILON), 3),
                "hop_strength": round(hop_strength, 3),
            })

            visited_txs.add(tx_id)
            next_account = outflow_row["receiver_account_id"]
            if next_account not in visited_accounts:
                frontier.append((next_account, out_amount, out_ts, depth + 1))

    # Overall lineage strength
    if hop_scores:
        lineage_strength = float(np.mean(hop_scores))
        max_depth_reached = max(c["depth"] for c in candidate_txs)
    else:
        lineage_strength = 0.0
        max_depth_reached = 0

    # Build reason string
    if candidate_txs:
        reason = (
            f"Found {len(candidate_txs)} candidate downstream transaction(s) "
            f"across {max_depth_reached} hop(s). "
            f"Signals: temporal proximity and amount relationship (not confirmed)."
        )
    else:
        reason = "No candidate downstream transactions found within proximity window."

    return {
        "origin_transaction": origin_transaction_id,
        "origin_receiver": origin_receiver,
        "candidate_downstream_transactions": candidate_txs,
        "depth": max_depth_reached,
        "lineage_strength": round(lineage_strength, 3),
        "reason": reason,
        "lineage_type": "potential_downstream_lineage",
        "disclaimer": "This is a heuristic estimate based on temporal proximity and amount relationships. Not a confirmed fund trace.",
    }
