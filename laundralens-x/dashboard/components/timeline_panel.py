"""
LaundraLens X — Timeline Panel Component
Renders chronological transaction sequences with visual indicators and forensic annotations.
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Any


def render_timeline_panel(events: List[Dict[str, Any]]):
    """Render the chronological transaction event stream."""
    st.markdown('<div class="ll-card-title">📅 CHRONOLOGICAL TRANSACTION FLOW</div>', unsafe_allow_html=True)

    if not events:
        st.caption("No events recorded for current observation window.")
        return

    for ev in events:
        is_inflow = (ev.get("direction") == "inflow")
        amt_str = ev.get("amount_inr_str", "")
        time_str = ev.get("time_str", "")
        counterparty = ev.get("counterparty_id", "")
        channel = ev.get("channel", "")
        annotations = ev.get("annotations", [])

        color = "#047857" if is_inflow else "#c01549"
        dir_symbol = "+ INFLOW" if is_inflow else "- OUTFLOW"

        ann_html = "".join([f'<span class="timeline-annotation">{a}</span>' for a in annotations])

        st.markdown(
            f'<div class="timeline-event">'
            f'<span class="timeline-time">{time_str}</span>'
            f'<span style="color:{color}; font-weight:600; min-width:85px;">{dir_symbol}</span>'
            f'<span style="font-weight:600; color:#0d253d; min-width:90px;" class="tnum">{amt_str}</span>'
            f'<span style="color:#64748d; font-size:12px;">via {channel} &bull; Counterparty: <code>{counterparty}</code></span>'
            f'{ann_html}'
            f'</div>',
            unsafe_allow_html=True,
        )
