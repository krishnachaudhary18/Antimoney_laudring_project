"""
LaundraLens X — Case Queue Component
Renders the left sidebar case triage queue with risk band filters and quick actions.
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Any, Callable


def render_case_queue(alerts: List[Dict[str, Any]], on_select: Callable[[str], None]):
    """Render the sidebar case triage queue."""
    st.markdown("### 📋 Case Triage Queue")

    if not alerts:
        st.info("No active alerts in queue.")
        return

    # Filter controls
    selected_band = st.selectbox(
        "Filter Risk Band",
        options=["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        index=0,
        label_visibility="collapsed",
    )

    filtered = alerts
    if selected_band != "ALL":
        filtered = [a for a in alerts if a.get("risk_band") == selected_band]

    st.caption(f"Showing {len(filtered)} alerts")

    # Badges and buttons
    band_emojis = {
        "CRITICAL": "🔴",
        "HIGH": "🟠",
        "MEDIUM": "🟡",
        "LOW": "⚪",
    }

    for alert in filtered:
        aid = alert.get("alert_id", "")
        acc_id = alert.get("account_id", "")
        band = alert.get("risk_band", "LOW")
        score = alert.get("priority_score", 0.0)
        emoji = band_emojis.get(band, "⚪")

        label = f"{emoji} {aid} · {acc_id} ({score:.0f})"

        is_selected = (st.session_state.get("selected_alert_id") == aid)

        if st.button(
            label,
            key=f"queue_item_{aid}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            on_select(aid)
