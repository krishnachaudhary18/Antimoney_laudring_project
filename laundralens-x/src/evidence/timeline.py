"""
LaundraLens X — Forensic Timeline Builder
Creates chronological sequence of events with behavioral and transaction annotations.
"""
from __future__ import annotations

from typing import List, Dict, Any
import pandas as pd


class TimelineBuilder:
    @staticmethod
    def build_events(txs: List[Dict[str, Any]], focus_account_id: str) -> List[Dict[str, Any]]:
        events = []
        for t in sorted(txs, key=lambda x: x["timestamp"]):
            is_inflow = (t.get("receiver_account_id") == focus_account_id)
            amt = float(t.get("amount", 0.0))
            ts = pd.to_datetime(t.get("timestamp"))

            annotations = []
            if amt >= 500000:
                annotations.append("High Value Transfer")
            if is_inflow:
                annotations.append("Primary Inflow")
            else:
                annotations.append("Rapid Outflow")

            events.append({
                "timestamp": ts.isoformat(),
                "time_str": ts.strftime("%H:%M"),
                "direction": "inflow" if is_inflow else "outflow",
                "amount": amt,
                "amount_inr_str": f"Rs {amt/100000:.1f}L" if amt >= 100000 else f"Rs {amt:,.0f}",
                "counterparty": t.get("sender_account_id") if is_inflow else t.get("receiver_account_id"),
                "channel": t.get("channel", "UPI"),
                "annotations": annotations,
            })
        return events
