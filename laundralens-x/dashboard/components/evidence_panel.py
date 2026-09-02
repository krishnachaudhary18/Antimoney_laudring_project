"""
LaundraLens X — Evidence Panel Component
Displays the forensic evidence ledger with exact calculations, facts, and provenance.
"""
from __future__ import annotations

import streamlit as st
from typing import List, Dict, Any


def render_evidence_panel(evidence_items: List[Dict[str, Any]]):
    """Render the forensic evidence ledger."""
    st.markdown("#### 📎 Forensic Evidence Ledger")
    st.caption("All findings are mapped directly to underlying database records, transaction hashes, and mathematical formulas.")

    if not evidence_items:
        st.info("No evidence items generated yet. Run the autonomous investigation first.")
        return

    for ev in evidence_items:
        eid = ev.get("evidence_id", "EV-UNKNOWN")
        etype = ev.get("evidence_type", "observation").upper()
        source = ev.get("source", "system")
        calc = ev.get("calculation")
        expl = ev.get("explanation")
        val = ev.get("value")

        with st.expander(f"📌 {eid} — [{etype}] Source: {source}"):
            if expl:
                st.markdown(f"**Forensic Note:** {expl}")
            if calc:
                st.markdown(f"**Formula / Calculation:**")
                st.code(calc, language="text")
            if val:
                st.json(val)
