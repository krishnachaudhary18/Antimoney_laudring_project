"""
LaundraLens X — Real-Time Transaction Radar Component
Displays live streaming transactions with color-coded risk alerts and velocity counters.
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Any


def render_stream_radar(recent_events: List[Dict[str, Any]]):
    """Render the real-time live transaction ticker."""
    st.markdown('<div class="ll-card-title">📡 REAL-TIME PAYMENT STREAM RADAR</div>', unsafe_allow_html=True)
    st.caption("Sliding-window monitor intercepting live payment webhook events. Detects sudden velocity bursts before batch settlement.")

    if not recent_events:
        st.info("Live payment stream connecting... Click refresh to pull recent buffered packets.")
        return

    # Metric counter
    anomalies = [e for e in recent_events if e.get("is_anomalous")]
    col1, col2, col3 = st.columns(3)
    col1.metric("Recent Packets Monitored", len(recent_events))
    col2.metric("Velocity Spikes Flagged", len(anomalies))
    col3.metric("Stream Status", "LIVE 🟢")

    st.markdown("---")

    for ev in recent_events[:10]:
        is_ano = ev.get("is_anomalous", False)
        border_color = "rgba(234,34,97,0.3)" if is_ano else "var(--color-hairline)"
        bg_color = "rgba(234,34,97,0.04)" if is_ano else "#ffffff"

        badge = '<span class="pill-tag-soft badge-critical">VELOCITY SPIKE</span>' if is_ano else '<span class="pill-tag-soft badge-success">NORMAL</span>'

        st.markdown(
            f'<div style="border:1px solid {border_color}; background:{bg_color}; border-radius:8px; padding:8px 12px; margin-bottom:6px; display:flex; justify-content:space-between; align-items:center;">'
            f'<div>'
            f'<span style="font-family:monospace; color:#64748d; font-size:11px; margin-right:8px;">{ev.get("time_str")}</span>'
            f'<span style="font-weight:600; color:#0d253d; font-size:13px; margin-right:12px;" class="tnum">{ev.get("amount_formatted")}</span>'
            f'<span style="color:#64748d; font-size:12px;">{ev.get("channel")} &bull; <code>{ev.get("sender_account_id")}</code> &rarr; <code>{ev.get("receiver_account_id")}</code> ({ev.get("location")})</span>'
            f'</div>'
            f'<div>{badge}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
