"""
LaundraLens X — Transaction Network Component
Embeds interactive Pyvis network visualizer, network depth controls,
and expandable technical graph analytics.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from typing import Optional, Any


def render_graph_panel(
    graph_html: Optional[str],
    account_id: str,
    current_hops: int = 1,
    current_mode: str = "investigation",
    status: str = "READY",
    error_msg: Optional[str] = None,
    on_retry: Optional[Any] = None,
    node_count: Optional[int] = None,
    edge_count: Optional[int] = None,
):
    """Render the transaction network with explicit states: LOADING, READY, EMPTY, ERROR, TIMEOUT."""
    st.markdown('<div class="ll-card-title">🕸 TRANSACTION NETWORK</div>', unsafe_allow_html=True)
    
    sub_desc = (
        "Focused Investigation View: Showing target account at center, primary fund inflow, rapid outbound transfers, and candidate downstream movement."
        if current_mode == "investigation"
        else "Full Topological View: Broader background counterparty network (unfiltered)."
    )
    st.markdown(f'<div style="font-size:12px; color:#64748b; margin-top:-6px; margin-bottom:12px;">{sub_desc}</div>', unsafe_allow_html=True)

    if status == "LOADING":
        st.markdown(
            '<div style="height:450px; display:flex; flex-direction:column; align-items:center; justify-content:center;'
            'background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; color:#64748d; font-size:13px;">'
            '<div style="font-weight:600; color:#0f172a; margin-bottom:6px;">Expanding connected accounts...</div>'
            '<div>Analyzing transaction relationships and candidate downstream accounts</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    if status == "TIMEOUT":
        st.error("Network request timed out after 8 seconds.")
        if st.button("🔄 Retry Network Load", key=f"retry_timeout_{account_id}_{current_hops}_{current_mode}"):
            if on_retry:
                on_retry()
            st.rerun()
        return

    if status == "ERROR":
        st.error(f"Failed to generate transaction network: {error_msg or 'Backend error'}")
        if st.button("🔄 Retry Network Load", key=f"retry_err_{account_id}_{current_hops}_{current_mode}"):
            if on_retry:
                on_retry()
            st.rerun()
        return

    if status == "EMPTY" or not graph_html or "No connected transactions found" in (graph_html or ""):
        st.markdown(
            '<div style="height:420px; display:flex; flex-direction:column; align-items:center; justify-content:center;'
            'background:#ffffff; border:1px dashed #cbd5e1; border-radius:12px; color:#64748d; font-size:13.5px;">'
            '<div style="font-weight:600; color:#334155; margin-bottom:4px;">No connected accounts found for this case.</div>'
            '<div style="font-size:12px; color:#94a3b8;">This account has no outward or inward transfers within the selected network depth.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # READY State
    components.html(graph_html, height=520, scrolling=False)
    level_str = f"{current_hops} level" if current_hops == 1 else f"{current_hops} levels"
    mode_label = "Investigation View (Alert-Relevant)" if current_mode == "investigation" else "Full Network View (Unfiltered)"
    st.caption(
        f"**Mode:** `{mode_label}` | **Depth:** `{level_str}` around subject account `★ {account_id}`. "
        "Interactive: Click any node to open the live Account Details panel on the right. Hover edges for timestamp & amounts. Drag nodes to inspect flow clusters."
    )

    with st.expander("Technical Network Details", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Visible Accounts", node_count or "Dynamic")
        with c2:
            st.metric("Directed Transfers", edge_count or "Dynamic")
        with c3:
            st.metric("Network Depth", f"{current_hops}-hop radius")
        with c4:
            st.metric("Graph Mode", mode_label.split(" ")[0])
        st.caption(
            "Underlying analytics: NetworkX directed graph projection, Louvain community partition, relevance ranking layer, and Pyvis physics layout."
        )
