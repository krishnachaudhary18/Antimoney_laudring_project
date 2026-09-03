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
            '<div class="risk-score-card">'
            '<div class="risk-score-value-row">'
            '<span class="risk-score-number" style="color:#94a3b8;">—</span>'
            '<span class="risk-score-scale">/ 100</span>'
            '</div>'
            '<div style="font-size:12px; color:#64748d;">Awaiting autonomous investigation</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    score = inv_data.get("priority_score", 0.0)
    band = inv_data.get("risk_band", "LOW")
    badge_class = f"badge-{band.lower()}"

    st.markdown(
        f'<div class="risk-score-card">'
        f'<div class="risk-score-header">'
        f'<span class="ll-card-title" style="margin-bottom:0;">PRIORITY SCORE</span>'
        f'<span class="pill-tag-soft {badge_class}">{band}</span>'
        f'</div>'
        f'<div class="risk-score-value-row">'
        f'<span class="risk-score-number">{score:.1f}</span>'
        f'<span class="risk-score-scale">/ 100</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Multi-signal breakdown
    signals = inv_data.get("signals", {})
    if signals:
        st.markdown("<div class='ll-card-title' style='margin-top:12px; margin-bottom:8px;'>SIGNAL CONTRIBUTIONS</div>", unsafe_allow_html=True)

        signal_labels = {
            "flow": ("Flow Conservation", "redistribution ratio"),
            "temporal": ("Temporal Velocity", "burst compression"),
            "behavior": ("Behavioral Deviation", "baseline drift"),
            "graph": ("Graph Network", "mule / hub connectivity"),
        }

        for sig_key, (title, subtitle) in signal_labels.items():
            val = float(signals.get(sig_key, 0.0))
            pct = int(val * 100)
            bar_color = "#ea2261" if pct >= 75 else ("#f97316" if pct >= 50 else ("#f59e0b" if pct >= 25 else "#533afd"))

            st.markdown(
                f'<div style="margin-bottom:8px;">'
                f'<div style="display:flex; justify-content:space-between; font-size:12px; color:#273951; margin-bottom:3px;">'
                f'<span><b>{title}</b> <span style="color:#64748d; font-size:11px;">({subtitle})</span></span>'
                f'<span class="tnum" style="color:#0d253d; font-weight:600;">{pct}%</span></div>'
                f'<div style="background:#edf2f7; border-radius:9999px; height:6px; overflow:hidden;">'
                f'<div style="width:{pct}%; background:{bar_color}; height:100%; border-radius:9999px; transition:width 0.4s ease;"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
