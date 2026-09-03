"""
LaundraLens X — Graph Panel Component
Embeds interactive Pyvis network graphs and hop-level controls.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional


def render_graph_panel(graph_html: Optional[str], account_id: str, current_hops: int = 2):
    """Render the transaction network graph."""
    st.markdown('<div class="ll-card-title">🕸 TRANSACTION NETWORK GRAPH</div>', unsafe_allow_html=True)

    if graph_html:
        components.html(graph_html, height=450, scrolling=False)
        st.caption(f"Ego-network centered on <code>{account_id}</code> ({current_hops}-hop radius). Interactive: drag nodes, scroll to zoom, hover for transfer details.", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="height:420px; display:flex; align-items:center; justify-content:center;'
            'background:#ffffff; border:1px dashed #e3e8ee; '
            'border-radius:12px; color:#64748d; font-size:13px;">'
            'Transaction graph loading or awaiting case selection.'
            '</div>',
            unsafe_allow_html=True,
        )
