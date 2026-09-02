"""
LaundraLens X — All 19 Investigation Tools
Typed, read-only functions. Each returns structured JSON-compatible data.

SAFETY: No tool modifies data. No tool freezes accounts. Read-only.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
import networkx as nx

from sqlalchemy.orm import Session

from src.db.models import Account, Customer, Transaction, Alert, Investigation, Evidence


# ─── DATA LOADING HELPERS ─────────────────────────────────────────

def _load_transactions(db: Session) -> pd.DataFrame:
    """Load all transactions as DataFrame."""
    rows = db.query(Transaction).all()
    if not rows:
        return pd.DataFrame()
    data = [{
        "transaction_id": t.transaction_id,
        "timestamp": t.timestamp,
        "sender_account_id": t.sender_account_id,
        "receiver_account_id": t.receiver_account_id,
        "amount": float(t.amount),
        "currency": t.currency,
        "channel": t.channel,
        "transaction_type": t.transaction_type,
        "scenario_id": t.scenario_id,
        "ground_truth_pattern": t.ground_truth_pattern,
    } for t in rows]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# ─── TOOL IMPLEMENTATIONS ─────────────────────────────────────────

def get_account_profile(account_id: str, db: Session) -> Dict:
    """Tool: get_account_profile — account demographics and risk profile."""
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        return {"error": f"Account {account_id} not found"}
    return {
        "account_id": account.account_id,
        "customer_id": account.customer_id,
        "account_type": account.account_type,
        "segment": account.segment,
        "risk_profile": account.risk_profile,
        "status": account.status,
        "home_region": account.home_region,
        "creation_date": account.creation_date.isoformat() if account.creation_date else None,
        "is_synthetic_suspicious": account.is_synthetic_suspicious,
        "scenario_id": account.scenario_id,
    }


def get_customer_profile(customer_id: str, db: Session) -> Dict:
    """Tool: get_customer_profile — customer KYC attributes."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    return {
        "customer_id": customer.customer_id,
        "customer_type": customer.customer_type,
        "occupation_or_business_category": customer.occupation_or_business_category,
        "expected_activity_category": customer.expected_activity_category,
        "geographic_region": customer.geographic_region,
    }


def get_account_history(account_id: str, db: Session) -> Dict:
    """Tool: get_account_history — all historical transactions."""
    txs = db.query(Transaction).filter(
        (Transaction.sender_account_id == account_id) |
        (Transaction.receiver_account_id == account_id)
    ).order_by(Transaction.timestamp.asc()).all()

    records = [{
        "transaction_id": t.transaction_id,
        "timestamp": t.timestamp.isoformat(),
        "sender_account_id": t.sender_account_id,
        "receiver_account_id": t.receiver_account_id,
        "amount": float(t.amount),
        "channel": t.channel,
        "direction": "inflow" if t.receiver_account_id == account_id else "outflow",
    } for t in txs]

    total_inflow = sum(r["amount"] for r in records if r["direction"] == "inflow")
    total_outflow = sum(r["amount"] for r in records if r["direction"] == "outflow")

    return {
        "account_id": account_id,
        "transaction_count": len(records),
        "total_inflow": round(total_inflow, 2),
        "total_outflow": round(total_outflow, 2),
        "transactions": records,
    }


def get_recent_transactions(account_id: str, window: str, db: Session, alert_ts: datetime) -> Dict:
    """Tool: get_recent_transactions — transactions in a specific window."""
    window_map = {"15m": 15/60, "1h": 1, "6h": 6, "24h": 24, "3d": 72, "7d": 168}
    hours = window_map.get(window, 24)
    start = alert_ts - timedelta(hours=hours)

    txs = db.query(Transaction).filter(
        ((Transaction.sender_account_id == account_id) |
         (Transaction.receiver_account_id == account_id)),
        Transaction.timestamp >= start,
        Transaction.timestamp <= alert_ts,
    ).order_by(Transaction.timestamp.asc()).all()

    records = [{
        "transaction_id": t.transaction_id,
        "timestamp": t.timestamp.isoformat(),
        "sender_account_id": t.sender_account_id,
        "receiver_account_id": t.receiver_account_id,
        "amount": float(t.amount),
        "channel": t.channel,
        "direction": "inflow" if t.receiver_account_id == account_id else "outflow",
    } for t in txs]

    return {"account_id": account_id, "window": window, "count": len(records), "transactions": records}


def analyze_time_windows(account_id: str, transactions_df: pd.DataFrame, alert_ts: datetime) -> Dict:
    """Tool: analyze_time_windows — multi-window temporal analysis."""
    from src.features.temporal import compute_temporal_features
    return compute_temporal_features(account_id, transactions_df, alert_ts)


def calculate_velocity(account_id: str, window: str, transactions_df: pd.DataFrame, alert_ts: datetime) -> Dict:
    """Tool: calculate_velocity — transaction velocity in a window."""
    from src.features.temporal import compute_window_features
    return compute_window_features(account_id, transactions_df, alert_ts, window)


def calculate_conservation(account_id: str, window: str, transactions_df: pd.DataFrame, alert_ts: datetime) -> Dict:
    """Tool: calculate_conservation — conservation ratio (flow analysis)."""
    from src.features.flow import compute_flow_features
    hours = {"24h": 24, "6h": 6, "1h": 1, "3d": 72}.get(window, 24)
    return compute_flow_features(account_id, transactions_df, alert_ts, primary_window_hours=hours)


def calculate_behavior_deviation(account_id: str, transactions_df: pd.DataFrame, alert_ts: datetime) -> Dict:
    """Tool: calculate_behavior_deviation — behavioral baseline deviation."""
    from src.features.behavioral import compute_behavioral_baseline, compute_current_deviation
    baseline = compute_behavioral_baseline(account_id, transactions_df, alert_ts)
    window_start = alert_ts - timedelta(hours=24)
    current = transactions_df[
        (transactions_df["timestamp"] >= window_start) &
        (transactions_df["timestamp"] <= alert_ts)
    ]
    deviation = compute_current_deviation(account_id, current, baseline)
    return {"baseline": baseline, "deviation": deviation}


def build_subgraph(account_id: str, hops: int, G: nx.DiGraph) -> Dict:
    """Tool: build_subgraph — k-hop subgraph data."""
    from src.graph.traversal import expand_k_hop
    return expand_k_hop(G, account_id, hops)


def expand_k_hop_tool(account_id: str, hops: int, G: nx.DiGraph) -> Dict:
    """Tool: expand_k_hop — expand graph neighborhood."""
    from src.graph.traversal import expand_k_hop
    return expand_k_hop(G, account_id, hops)


def find_paths_tool(source: str, target: str, max_depth: int, G: nx.DiGraph) -> Dict:
    """Tool: find_paths — find transaction paths."""
    from src.graph.traversal import find_paths
    return find_paths(G, source, target, max_depth)


def trace_potential_lineage_tool(
    transaction_id: str, depth: int, transactions_df: pd.DataFrame
) -> Dict:
    """Tool: trace_potential_lineage — heuristic fund lineage."""
    from src.graph.lineage import trace_potential_lineage
    return trace_potential_lineage(transaction_id, transactions_df, max_depth=depth)


def get_connected_entities_tool(account_id: str, G: nx.DiGraph) -> Dict:
    """Tool: get_connected_entities — weakly connected component."""
    from src.graph.traversal import get_connected_entities
    return get_connected_entities(G, account_id)


def get_model_scores(account_id: str, feature_vector: list) -> Dict:
    """Tool: get_model_scores — all ML model scores."""
    from src.models.model_registry import registry
    if not registry.models_loaded:
        registry.load_all()
    scores = registry.score_all(feature_vector)
    return {"account_id": account_id, "model_scores": scores}


def get_feature_contributions(feature_vector: list) -> Dict:
    """Tool: get_feature_contributions — SHAP values from XGBoost."""
    from src.models.model_registry import registry
    if not registry.models_loaded:
        registry.load_all()
    shap = registry.get_shap_values(feature_vector)
    return {"shap_contributions": shap, "source": "xgboost_shap" if shap else "unavailable"}


def generate_counterfactual_tool(signals: Dict[str, float], base_score: float) -> Dict:
    """Tool: generate_counterfactual — score sensitivity analysis."""
    from src.risk.scorer import compute_counterfactual
    sensitivity = compute_counterfactual(signals, base_score)
    return {
        "sensitivity": sensitivity,
        "label": "Score sensitivity",
        "disclaimer": "Shows signal contribution. Does not establish causation.",
    }


def create_timeline(case_id: str, account_id: str, transactions_df: pd.DataFrame, alert_ts: datetime) -> Dict:
    """Tool: create_timeline — chronological annotated timeline."""
    from datetime import timedelta
    window = alert_ts - timedelta(hours=24)
    relevant = transactions_df[
        ((transactions_df["sender_account_id"] == account_id) |
         (transactions_df["receiver_account_id"] == account_id)) &
        (transactions_df["timestamp"] >= window) &
        (transactions_df["timestamp"] <= alert_ts + timedelta(hours=4))
    ].sort_values("timestamp")

    events = []
    for _, row in relevant.iterrows():
        is_inflow = row["receiver_account_id"] == account_id
        amount = float(row["amount"])
        ts = pd.Timestamp(row["timestamp"])

        annotations = []
        if amount > 500000:
            annotations.append("large_amount")
        if is_inflow and amount > 500000:
            annotations.append("large_inflow")
        if not is_inflow and amount > 100000:
            annotations.append("significant_outflow")
        if row.get("ground_truth_pattern") == "synthetic_suspicious_pattern":
            annotations.append("suspicious_pattern")

        # Format INR amount
        if amount >= 100000:
            amount_str = f"Rs {amount/100000:.1f}L"
        else:
            amount_str = f"Rs {amount:,.0f}"

        events.append({
            "timestamp": ts.isoformat(),
            "time_str": ts.strftime("%H:%M"),
            "direction": "inflow" if is_inflow else "outflow",
            "amount": amount,
            "amount_inr_str": amount_str,
            "counterparty_id": row["sender_account_id"] if is_inflow else row["receiver_account_id"],
            "channel": row.get("channel", ""),
            "transaction_id": row.get("transaction_id", ""),
            "annotations": annotations,
        })

    return {"case_id": case_id, "account_id": account_id, "events": events, "count": len(events)}


def collect_evidence(case_id: str, account_id: str, findings: List[Dict]) -> List[Dict]:
    """Tool: collect_evidence — structured evidence from findings."""
    evidence_list = []
    for i, finding in enumerate(findings):
        evidence_list.append({
            "evidence_id": f"E-{case_id[-4:]}-{i+1:03d}",
            "case_id": case_id,
            "evidence_type": finding.get("category", "unknown"),
            "account_id": account_id,
            "transaction_id": finding.get("primary_transaction_id"),
            "source": finding.get("source_tool", "orchestrator"),
            "value": finding.get("data", {}),
            "calculation": finding.get("calculation"),
            "explanation": finding.get("explanation"),
        })
    return evidence_list
