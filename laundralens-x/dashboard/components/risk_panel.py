"""
LaundraLens X — Risk Panel Component
Renders the Investigation Priority Score, risk band badge, and multi-signal metrics.
"""
from __future__ import annotations

import streamlit as st
from typing import Dict, Any


def render_risk_panel(inv_data: Dict[str, Any]):
    """Render the primary risk score and signal breakdown."""
    st.markdown('<div class="ll-card-title">⚡ INVESTIGATION PRIORITY</div>', unsafe_allow_html=True)

    if not inv_data or not inv_data.get("priority_score"):
        st.markdown(
            '<div class="risk-score-display">'
            '<div class="risk-score-number" style="-webkit-text-fill-color:#475569;">—</div>'
            '<div class="risk-score-label">Awaiting Autonomous Run</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    score = inv_data.get("priority_score", 0.0)
    band = inv_data.get("risk_band", "LOW")

    band_colors = {
        "CRITICAL": "#ef4444",
        "HIGH": "#f97316",
        "MEDIUM": "#f59e0b",
        "LOW": "#6b7280",
    }
    color = band_colors.get(band, "#6b7280")

    st.markdown(
        f'<div class="risk-score-display">'
        f'<div class="risk-score-number" style="background:linear-gradient(135deg, {color}, {color}88);'
        f'-webkit-background-clip:text; -webkit-text-fill-color:transparent;">{score:.1f}</div>'
        f'<div class="risk-score-label">/ 100 — <span style="color:{color}; font-weight:bold;">{band}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Multi-signal breakdown
    signals = inv_data.get("signals", {})
    if signals:
        st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)
        st.markdown("**Forensic Signals Breakdown:**")

        signal_labels = {
            "flow": ("Flow Conservation", "redistribution ratio"),
            "temporal": ("Temporal Velocity", "compressed bursts"),
            "behavior": ("Behavioral Deviation", "historical baseline deviation"),
            "graph": ("Graph Network", "counterparty hub topology"),
        }

        for sig_key, (title, subtitle) in signal_labels.items():
            val = float(signals.get(sig_key, 0.0))
            pct = int(val * 100)
            bar_color = "#ef4444" if pct >= 75 else ("#f97316" if pct >= 50 else ("#f59e0b" if pct >= 25 else "#3b82f6"))

            st.markdown(
                f'<div style="margin-bottom:0.6rem;">'
                f'<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#94a3b8; margin-bottom:2px;">'
                f'<span><b>{title}</b> ({subtitle})</span><span><b>{pct}%</b></span></div>'
                f'<div style="background:#1a2540; border-radius:4px; height:6px; overflow:hidden;">'
                f'<div style="width:{pct}%; background:{bar_color}; height:100%; border-radius:4px; transition:width 0.4s ease;"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
