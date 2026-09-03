"""
LaundraLens X — Explanation Panel Component
Renders the SHAP feature contribution waterfall and analyst plain-language narratives.
"""
from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Any


def render_explanation_panel(shap_contributions: Dict[str, float], explanations: List[Dict[str, Any]]):
    """Render the SHAP waterfall and WHY narratives."""
    st.markdown("#### ❓ Explainability & Model Attribution")

    if shap_contributions:
        features = list(shap_contributions.keys())[:10]
        values = [shap_contributions[f] for f in features]
        colors = ["#ea2261" if v > 0 else "#10b981" for v in values]

        fig = go.Figure(go.Bar(
            x=values,
            y=features,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.3f}" for v in values],
            textposition="outside",
        ))
        fig.update_layout(
            title=dict(text="Tree Feature Attributions (SHAP)", font=dict(size=13, color="#0d253d", family="Inter")),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#273951",
            font_family="Inter",
            height=320,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(gridcolor="#edf2f7", zerolinecolor="#cbd5e1", tickfont=dict(size=11, color="#64748d")),
            yaxis=dict(tickfont=dict(size=11, color="#273951"), autorange="reversed"),
        )
        st.plotly_chart(fig, width='stretch')

    if explanations:
        st.markdown("**Analyst Key Observations:**")
        for item in explanations:
            st.markdown(
                f'<div class="evidence-item">'
                f'<b>{item.get("signal", "")}</b> &mdash; {item.get("description", "")}'
                f'</div>',
                unsafe_allow_html=True,
            )
