"""
LaundraLens X — Case Report & SAR Generation Component
Renders the audit-ready investigation report and one-click export actions.
"""
from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Callable


def render_case_panel(report_data: Dict[str, Any], on_generate_report: Callable[[], None]):
    """Render the formal case report and SAR draft."""
    st.markdown("#### 📄 Formal Investigation & SAR Report")

    if not report_data:
        st.info("No formal report has been compiled yet.")
        if st.button("✨ Compile Formal Case Report (Gemini Flash)", type="primary"):
            on_generate_report()
        return

    st.markdown(
        '<div class="ll-card" style="border-color:rgba(139,92,246,0.3);">'
        '<div class="ll-card-title">🤖 AI-GENERATED INVESTIGATION REPORT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(report_data.get("full_text", report_data.get("body", "Report unavailable.")))

    st.markdown(
        '<div style="margin-top:1rem; padding:0.6rem; background:rgba(245,158,11,0.1);'
        'border:1px solid rgba(245,158,11,0.3); border-radius:6px; font-size:0.75rem; color:#fcd34d;">'
        '⚠ This report is compiled for investigative decision support only. All filings require human compliance review. '
        'Generated from synthetic demonstration data.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Download report button
    report_text = report_data.get("full_text", report_data.get("body", ""))
    st.download_button(
        "⬇ Download SAR Markdown Dossier",
        data=report_text,
        file_name="investigation_report.md",
        mime="text/markdown",
    )
