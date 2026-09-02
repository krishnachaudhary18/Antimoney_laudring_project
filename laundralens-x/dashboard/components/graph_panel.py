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
        st.caption(f"Ego-network centered on `{account_id}` ({current_hops}-hop radius). Interactive: drag nodes, scroll to zoom, hover for transfer details.")
    else:
        st.markdown(
            '<div style="height:420px; display:flex; align-items:center; justify-content:center;'
            'background:rgba(17,26,46,0.8); border:1px dashed rgba(255,255,255,0.1); '
            'border-radius:12px; color:#475569; font-size:0.9rem;">'
            'Transaction graph loading or awaiting case selection.'
            '</div>',
            unsafe_allow_html=True,
        )
