"""
LaundraLens X — Adaptive Investigation Planner
Dynamically evaluates intermediate forensic signals and directs investigative branching.
"""
from __future__ import annotations

from typing import Dict, List, Any


class AdaptivePlanner:
    """
    Evaluates intermediate signals and determines investigative actions,
    branching depths, and targeted forensic dives.
    """

    def __init__(self):
        self.decisions_log: List[Dict[str, Any]] = []

    def evaluate_initial_plan(self, account_profile: Dict, alert_summary: str) -> Dict[str, Any]:
        """Formulate initial investigative plan based on subject profile and alert metadata."""
        plan = {
            "initial_depth": 2,
            "target_windows": ["1h", "24h"],
            "focus_areas": ["temporal_velocity", "flow_conservation"],
            "hypotheses": [],
        }

        segment = account_profile.get("segment", "retail")
        acc_type = account_profile.get("account_type", "savings")

        if acc_type in ("savings", "student"):
            plan["hypotheses"].append("Potential mule or pass-through account given retail profile")
        elif segment in ("corporate", "sme"):
            plan["hypotheses"].append("Potential layering or trade-based structuring hub")

        if "redistribution" in alert_summary.lower() or "conservation" in alert_summary.lower():
            plan["focus_areas"].append("lineage_tracing")
            plan["initial_depth"] = 3

        return plan

    def should_deep_dive_flow(self, flow_signal: float, conservation_ratio: float) -> bool:
        """Determine if fund conservation warrants deeper flow analysis."""
        decision = flow_signal > 0.5 or conservation_ratio > 0.70
        self.decisions_log.append({
            "stage": "flow_analysis",
            "decision": "deep_dive_flow",
            "value": decision,
            "reason": f"flow_signal={flow_signal:.3f}, conservation_ratio={conservation_ratio:.3f}"
        })
        return decision

    def determine_graph_expansion(self, fan_out: int, new_recipient_ratio: float) -> int:
        """Dynamically select graph expansion radius."""
        if fan_out >= 8 or new_recipient_ratio >= 0.7:
            hops = 3
        elif fan_out >= 3 or new_recipient_ratio >= 0.4:
            hops = 2
        else:
            hops = 1

        self.decisions_log.append({
            "stage": "graph_analysis",
            "decision": f"expand_{hops}_hops",
            "value": hops,
            "reason": f"fan_out={fan_out}, new_recipient_ratio={new_recipient_ratio:.2f}"
        })
        return hops

    def should_scan_syndicates(self, graph_signal: float, fan_in: int, fan_out: int) -> bool:
        """Determine whether to run multi-account syndicate and circular cycle detection."""
        decision = graph_signal > 0.35 or (fan_in >= 2 and fan_out >= 2) or (fan_in >= 4)
        self.decisions_log.append({
            "stage": "syndicate_analysis",
            "decision": "scan_syndicate_topology",
            "value": decision,
            "reason": f"graph_signal={graph_signal:.3f}, fan_in={fan_in}, fan_out={fan_out}"
        })
        return decision

    def select_lineage_roots(self, account_id: str, transactions_df, alert_timestamp) -> List[str]:
        """
        Dynamically identify candidate root transactions to trace downstream.
        Prioritizes the largest inflows received within 48h prior to alert.
        """
        if transactions_df is None or transactions_df.empty:
            return []

        import pandas as pd
        from datetime import timedelta

        df = transactions_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        window_start = alert_timestamp - timedelta(hours=48)

        inflows = df[
            (df["receiver_account_id"] == account_id) &
            (df["timestamp"] >= window_start) &
            (df["timestamp"] <= alert_timestamp)
        ].sort_values("amount", ascending=False)

        if not inflows.empty:
            return inflows["transaction_id"].head(3).tolist()

        # Fallback: any historical inflow
        any_inflow = df[
            (df["receiver_account_id"] == account_id) &
            (df["timestamp"] <= alert_timestamp)
        ].sort_values("amount", ascending=False)

        if not any_inflow.empty:
            return [any_inflow.iloc[0]["transaction_id"]]

        return []
