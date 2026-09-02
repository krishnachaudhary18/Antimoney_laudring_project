"""
LaundraLens X — Streamlit Dashboard Main Application
Premium dark-mode analyst workstation interface.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import requests
from datetime import datetime

# --- Page Config (must be first Streamlit call) ---
st.set_page_config(
    page_title="LaundraLens X — Financial Crime Investigation",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load CSS ---
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Constants ---
API_BASE = "http://localhost:8000/api/v1"

# --- Session State Defaults ---
if "selected_case_id" not in st.session_state:
    st.session_state.selected_case_id = "CASE-DEMO-001"
if "selected_alert_id" not in st.session_state:
    st.session_state.selected_alert_id = "ALERT-DEMO-001"
if "investigation_running" not in st.session_state:
    st.session_state.investigation_running = False
if "investigation_data" not in st.session_state:
    st.session_state.investigation_data = None
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "graph"


def api_get(path: str, default=None):
    """Safe API GET with error handling."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return default


def api_post(path: str, payload: dict, default=None):
    """Safe API POST with error handling."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return default


def render_header():
    """Render the LaundraLens X header bar."""
    st.markdown("""
    <div class="ll-header">
        <div class="ll-logo">🔍 LaundraLens X</div>
        <div style="display:flex; align-items:center; gap:1rem;">
            <span class="ll-watermark">⚠ SYNTHETIC DEMONSTRATION DATA</span>
            <span style="color:#475569; font-size:0.8rem;">v1.0.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with case queue and controls."""
    with st.sidebar:
        st.markdown("### 📋 Case Queue")

        # Fetch alerts
        alerts = api_get("/alerts", default=[])

        if not alerts:
            st.warning("No alerts loaded. Run the data pipeline first.")
            st.code("python scripts/seed_database.py", language="bash")
            return

        # Group by risk band
        bands = {
            "CRITICAL": [a for a in alerts if a.get("risk_band") == "CRITICAL"],
            "HIGH": [a for a in alerts if a.get("risk_band") == "HIGH"],
            "MEDIUM": [a for a in alerts if a.get("risk_band") == "MEDIUM"],
            "LOW": [a for a in alerts if a.get("risk_band") == "LOW"],
        }

        colors = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "⚪"}

        for band, band_alerts in bands.items():
            if band_alerts:
                st.markdown(f"**{colors[band]} {band}** — {len(band_alerts)} cases")
                for alert in band_alerts[:5]:  # Show top 5 per band
                    case_label = f"{alert.get('alert_id', '?')} · {alert.get('account_id', '?')}"
                    if st.button(
                        case_label,
                        key=f"btn_{alert.get('alert_id')}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_alert_id = alert.get("alert_id")
                        st.session_state.investigation_data = None
                        st.rerun()

        st.divider()

        # Demo Controls
        st.markdown("### ⚙ Demo Controls")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶ RUN", use_container_width=True, type="primary"):
                st.session_state.investigation_running = True
                st.rerun()
        with col2:
            if st.button("↺ RESET", use_container_width=True):
                st.session_state.investigation_data = None
                st.session_state.investigation_running = False
                st.rerun()

        if st.button("⚙ REGENERATE", use_container_width=True):
            st.info("Regenerating scenario... run `python scripts/seed_database.py`")

        st.divider()

        # API Status
        health = api_get("/health")
        if health:
            st.success(f"✅ API Online")
        else:
            st.error("❌ API Offline — start with: `uvicorn src.api.main:app --reload`")

        st.markdown(
            f"<div style='font-size:0.65rem; color:#475569; margin-top:1rem;'>"
            f"LaundraLens X · Razorpay Hackathon 2026<br>"
            f"⚠ Synthetic data only. Not real financial data.</div>",
            unsafe_allow_html=True,
        )


def render_main_area():
    """Render the main investigation workspace."""
    render_header()

    # Main 3-column layout
    col_left, col_center, col_right = st.columns([2, 4, 3])

    with col_left:
        render_investigation_panel()

    with col_center:
        render_graph_panel()

    with col_right:
        render_risk_score_panel()

    # Bottom panels
    st.divider()
    render_timeline_panel()

    st.divider()
    # Bottom tabs: Evidence | WHY | Sensitivity | Case Report | Disposition | Playground
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📎 Evidence Ledger",
        "❓ WHY? Attribution",
        "📊 Score Sensitivity",
        "📄 SAR Report & Dossier",
        "⚖ Analyst Disposition",
        "🧪 Scenario Playground",
    ])

    with tab1:
        render_evidence_panel()
    with tab2:
        render_explanation_panel()
    with tab3:
        render_sensitivity_panel()
    with tab4:
        render_case_report_panel()
    with tab5:
        render_disposition_panel()
    with tab6:
        render_scenario_playground_panel()


def render_investigation_panel():
    """AI Investigator progress panel."""
    st.markdown('<div class="ll-card-title">🤖 AI INVESTIGATOR</div>', unsafe_allow_html=True)

    alert_id = st.session_state.selected_alert_id
    inv_data = st.session_state.investigation_data

    if st.session_state.investigation_running and not inv_data:
        with st.spinner("Starting investigation..."):
            result = api_post("/investigations", {"alert_id": alert_id})
            if result:
                st.session_state.investigation_data = result
                st.session_state.investigation_running = False
                st.rerun()
            else:
                st.session_state.investigation_running = False
                st.error("Investigation failed. Ensure API is running and database is seeded.")

    if not inv_data:
        st.markdown(
            '<div style="color:#475569; font-size:0.9rem; padding:1rem 0;">'
            'Click ▶ RUN in the sidebar to start the investigation.</div>',
            unsafe_allow_html=True,
        )
        return

    # Show progress steps
    steps = inv_data.get("progress_steps", [])
    status = inv_data.get("status", "unknown")

    default_steps = [
        ("Loading account history", True),
        ("Establishing baseline", True),
        ("Analyzing temporal windows", True),
        ("Measuring fund redistribution", True),
        ("Building transaction graph", True),
        ("Expanding connected entities", True),
        ("Tracing potential lineage", True),
        ("Running model analysis", True),
        ("Collecting evidence", True),
        ("Preparing findings", True),
        ("Generating report", status == "REPORT_READY"),
    ]

    for step_name, done in default_steps:
        icon = "✅" if done else "⏳"
        color = "#10b981" if done else "#f59e0b"
        st.markdown(
            f'<div class="progress-step {"done" if done else "active"}">'
            f'<span>{icon}</span><span style="color:{color}">{step_name}</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown(f"<br><b>Status:</b> <code>{status}</code>", unsafe_allow_html=True)


def render_graph_panel():
    """Transaction graph visualization via Pyvis."""
    st.markdown('<div class="ll-card-title">🕸 TRANSACTION GRAPH</div>', unsafe_allow_html=True)

    account_id = None
    alert_id = st.session_state.selected_alert_id
    if alert_id:
        alert = api_get(f"/alerts/{alert_id}")
        if alert:
            account_id = alert.get("account_id")

    if not account_id:
        st.info("Select a case from the sidebar to view the transaction graph.")
        return

    graph_data = api_get(f"/graph/{account_id}?hops=2")
    if graph_data and graph_data.get("html"):
        import streamlit.components.v1 as components
        components.html(graph_data["html"], height=450, scrolling=False)
    else:
        # Placeholder while graph module initializes
        st.markdown(
            '<div style="height:420px; display:flex; align-items:center; justify-content:center;'
            'background:rgba(17,26,46,0.8); border:1px dashed rgba(255,255,255,0.1); '
            'border-radius:12px; color:#475569; font-size:0.9rem;">'
            '🕸 Graph renders after database is seeded and graph module is initialized.'
            '</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Account: `{account_id}` · k-hop: 2")


def render_risk_score_panel():
    """Investigation Priority Score display."""
    st.markdown('<div class="ll-card-title">⚡ INVESTIGATION PRIORITY</div>', unsafe_allow_html=True)

    inv_data = st.session_state.investigation_data
    if not inv_data or not inv_data.get("priority_score"):
        st.markdown(
            '<div class="risk-score-display">'
            '<div class="risk-score-number" style="-webkit-text-fill-color:#475569;">—</div>'
            '<div class="risk-score-label">Awaiting Investigation</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    score = inv_data.get("priority_score", 0)
    band = inv_data.get("risk_band", "LOW")
    band_color = {
        "CRITICAL": "#ef4444", "HIGH": "#f97316",
        "MEDIUM": "#f59e0b", "LOW": "#6b7280"
    }.get(band, "#6b7280")

    st.markdown(
        f'<div class="risk-score-display">'
        f'<div class="risk-score-number" style="background:linear-gradient(135deg,{band_color},{band_color}88);'
        f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;">{score:.0f}</div>'
        f'<div class="risk-score-label">/ 100 — {band}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Signal bars
    signals = inv_data.get("signals", {})
    if signals:
        st.markdown("<br>", unsafe_allow_html=True)
        for signal_name, value in signals.items():
            pct = int(value * 100)
            bar_color = "#ef4444" if pct >= 80 else "#f97316" if pct >= 60 else "#f59e0b"
            st.markdown(
                f'<div style="margin-bottom:0.5rem;">'
                f'<div style="display:flex;justify-content:space-between;font-size:0.75rem;color:#94a3b8;margin-bottom:3px;">'
                f'<span>{signal_name.title()}</span><span>{pct}%</span></div>'
                f'<div style="background:#1a2540;border-radius:4px;height:6px;">'
                f'<div style="width:{pct}%;background:{bar_color};border-radius:4px;height:6px;'
                f'transition:width 0.5s ease;"></div></div></div>',
                unsafe_allow_html=True,
            )


def render_timeline_panel():
    """Chronological transaction timeline."""
    st.markdown('<div class="ll-card-title">📅 INVESTIGATION TIMELINE</div>', unsafe_allow_html=True)

    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if case_id:
        timeline = api_get(f"/investigations/{case_id}/timeline")
        events = timeline.get("events", []) if timeline else []
    else:
        events = []

    if not events:
        st.caption("Timeline populates after investigation completes.")
        return

    # Render events
    for ev in events:
        direction = "+" if ev.get("direction") == "inflow" else "-"
        amount = ev.get("amount_inr_str", "")
        time_str = ev.get("time_str", "")
        counterparty = ev.get("counterparty_id", "")
        annotations = ev.get("annotations", [])

        ann_html = "".join(
            f'<span class="timeline-annotation">{a}</span>' for a in annotations
        )
        color = "#10b981" if direction == "+" else "#ef4444"

        st.markdown(
            f'<div class="timeline-event animate-in">'
            f'<span class="timeline-time">{time_str}</span>'
            f'<span style="color:{color};font-weight:700;">{direction}{amount}</span>'
            f'<span style="color:#475569;font-size:0.8rem;">→ {counterparty}</span>'
            f'{ann_html}</div>',
            unsafe_allow_html=True,
        )


def render_evidence_panel():
    """Evidence ledger display."""
    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if not case_id:
        st.caption("Evidence ledger populates after investigation completes.")
        return

    evidence = api_get(f"/investigations/{case_id}/evidence")
    items = evidence.get("evidence", []) if evidence else []

    if not items:
        st.caption("No evidence collected yet.")
        return

    for ev in items:
        with st.expander(f"📎 {ev.get('evidence_id', '?')} — {ev.get('evidence_type', '?')}"):
            st.markdown(f"**Source:** `{ev.get('source', 'unknown')}`")
            if ev.get("calculation"):
                st.markdown(
                    f'<div class="evidence-calculation">{ev["calculation"]}</div>',
                    unsafe_allow_html=True,
                )
            if ev.get("explanation"):
                st.info(ev["explanation"])
            if ev.get("value"):
                st.json(ev["value"])


def render_explanation_panel():
    """WHY panel — SHAP + signal explanations."""
    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if not case_id:
        st.caption("Explanations populate after investigation completes.")
        return

    expl = api_get(f"/investigations/{case_id}/explanations")
    if not expl or not expl.get("explanations"):
        st.caption("No explanations available yet.")
        return

    # SHAP waterfall chart via Plotly
    shap_data = expl.get("shap_contributions", {})
    if shap_data:
        import plotly.graph_objects as go
        features = list(shap_data.keys())[:10]
        values = [shap_data[f] for f in features]
        colors = ["#ef4444" if v > 0 else "#10b981" for v in values]

        fig = go.Figure(go.Bar(
            x=values, y=features, orientation='h',
            marker_color=colors,
            text=[f"{v:+.3f}" for v in values],
            textposition='outside',
        ))
        fig.update_layout(
            title="Feature Contributions (SHAP)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(17,26,46,0.5)',
            font_color='#94a3b8',
            font_family='Inter',
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Human-readable explanations
    for item in expl.get("explanations", []):
        st.markdown(
            f'<div class="evidence-item animate-in">'
            f'<b>{item.get("signal", "")}</b> — {item.get("description", "")}'
            f'</div>',
            unsafe_allow_html=True,
        )


def render_sensitivity_panel():
    """WHAT-IF / Score Sensitivity panel."""
    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if not case_id:
        st.caption("Score sensitivity analysis populates after investigation completes.")
        return

    cf = api_get(f"/investigations/{case_id}/counterfactual")
    sensitivity = cf.get("sensitivity", {}) if cf else {}

    if not sensitivity:
        st.caption("No sensitivity data available yet.")
        return

    import plotly.graph_objects as go

    labels = list(sensitivity.keys())
    values = list(sensitivity.values())
    baseline = sensitivity.get("baseline", 0)
    colors = ["#6b7280" if k == "baseline" else "#3b82f6" for k in labels]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker_color=colors,
        text=[f"{v:.0f}" for v in values],
        textposition='outside',
    ))
    fig.add_hline(y=baseline, line_dash="dot", line_color="#ef4444", opacity=0.5)
    fig.update_layout(
        title="Score Sensitivity — How much does each signal contribute?",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(17,26,46,0.5)',
        font_color='#94a3b8',
        font_family='Inter',
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(range=[0, 105], gridcolor='rgba(255,255,255,0.05)'),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠ Score sensitivity shows signal contribution, not causal certainty.")


def render_case_report_panel():
    """Gemini-powered case report panel."""
    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if not case_id:
        st.caption("Case report generates after investigation completes.")
        return

    case = api_get(f"/cases/{case_id}")

    if not case or not case.get("report"):
        if st.button("📄 Generate Case Report (Gemini)", type="primary"):
            with st.spinner("Generating evidence-grounded case report..."):
                result = api_post(f"/cases/{case_id}/report", {})
                if result:
                    st.rerun()
                else:
                    st.error("Report generation failed.")
        return

    report = case.get("report", {})

    st.markdown(
        '<div class="ll-card" style="border-color:rgba(139,92,246,0.3);">'
        '<div class="ll-card-title">🤖 AI-GENERATED INVESTIGATION REPORT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(f"**{report.get('case_id', case_id)}** · {report.get('risk_band', '—')}")
    st.markdown("---")
    st.markdown(report.get("executive_summary", ""))

    if report.get("key_findings"):
        st.markdown("**Key Findings**")
        for f in report.get("key_findings", []):
            st.markdown(f"- {f}")

    st.markdown(report.get("body", ""))

    st.markdown(
        '<div style="margin-top:1rem;padding:0.5rem;background:rgba(245,158,11,0.1);'
        'border:1px solid rgba(245,158,11,0.3);border-radius:6px;font-size:0.75rem;color:#fcd34d;">'
        '⚠ This report is generated for investigation support only. All actions require human review. '
        'Synthetic data — not real financial data.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Download Markdown button
    col_d1, col_d2 = st.columns(2)
    report_text = report.get("full_text", report.get("body", ""))
    with col_d1:
        st.download_button(
            "⬇ Download SAR Markdown Dossier",
            data=report_text,
            file_name=f"{case_id}_SAR_dossier.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_d2:
        dossier_html = api_get(f"/cases/{case_id}/dossier")
        if dossier_html:
            st.download_button(
                "⬇ Download Regulatory HTML Dossier (FIU-IND)",
                data=str(dossier_html),
                file_name=f"{case_id}_FIU_IND_dossier.html",
                mime="text/html",
                use_container_width=True,
            )


def render_disposition_panel():
    """Human-in-the-Loop Analyst Disposition Workflow."""
    st.markdown('<div class="ll-card-title">⚖ COMPLIANCE OFFICER DISPOSITION WORKFLOW</div>', unsafe_allow_html=True)
    inv_data = st.session_state.investigation_data
    case_id = inv_data.get("case_id") if inv_data else None

    if not case_id:
        st.caption("Run an autonomous investigation first to enable compliance decisioning.")
        return

    st.markdown(
        f"Record regulatory determination for case <code>{case_id}</code> "
        f"(Subject: <code>{inv_data.get('account_id')}</code>, Priority: <b>{inv_data.get('priority_score', 0):.1f}</b>).",
        unsafe_allow_html=True,
    )

    with st.form(key=f"disposition_form_{case_id}"):
        action = st.selectbox(
            "Select Regulatory Action",
            options=[
                "FILE_SAR",
                "REQUEST_INFO",
                "ENHANCED_DILIGENCE",
                "DISMISS_FALSE_POSITIVE",
            ],
            format_func=lambda x: {
                "FILE_SAR": "🚨 Formal Escalation: File SAR to Financial Intelligence Unit (FIU)",
                "REQUEST_INFO": "📨 Request for Information (RFI): Demand Proof of Funds",
                "ENHANCED_DILIGENCE": "🔍 Enhanced Due Diligence (EDD): Place on 30-Day Watchlist",
                "DISMISS_FALSE_POSITIVE": "✔ Dismiss: Documented Legitimate Commercial Flow",
            }.get(x, x),
        )

        col_a, col_b = st.columns(2)
        with col_a:
            analyst_id = st.text_input("Officer Identifier", value="OFFICER-7429")
        with col_b:
            reason_code = st.selectbox(
                "Regulatory Typology Code",
                options=[
                    "TYP-01: Rapid Passthrough Layering",
                    "TYP-02: High-Velocity Mule Ring",
                    "TYP-03: Funnel Account Smurfing",
                    "TYP-04: KYC Profile Misalignment",
                    "TYP-05: Legitimate Merchant Inflow",
                ],
            )

        notes = st.text_area(
            "Forensic Justification & Decision Notes",
            value=f"Automated priority score of {inv_data.get('priority_score', 0):.1f} driven by conservation ratio of {inv_data.get('signals', {}).get('flow', 0):.2f}. Action recommended based on corroboration across 3 ML architectures.",
            height=100,
        )

        submit_btn = st.form_submit_button("✍ Sign & Commit Regulatory Decision", type="primary", use_container_width=True)

    if submit_btn:
        payload = {
            "case_id": case_id,
            "action": action,
            "analyst_id": analyst_id,
            "reason_code": reason_code,
            "notes": notes,
        }
        res = api_post("/decisions", payload)
        if res:
            st.success(f"✔ Decision committed: {res.get('action')} — Status: {res.get('escalation_status')} (Ref: {res.get('decision_id')})")
        else:
            st.error("Failed to commit decision to audit trail.")

    # Show past audit trail
    history = api_get(f"/decisions/{case_id}", default=[])
    if history:
        st.markdown("**Case Decision Audit Trail:**")
        for d in history:
            st.markdown(
                f"<div class='evidence-item'>"
                f"<b>{d.get('action')}</b> by <code>{d.get('analyst_id')}</code> at {d.get('timestamp')}<br>"
                f"<span style='color:#94a3b8; font-size:0.8rem;'>Typology: {d.get('reason_code')} &bull; Status: {d.get('escalation_status')}</span><br>"
                f"<span style='font-size:0.85rem;'>{d.get('notes')}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )


def render_scenario_playground_panel():
    """Interactive Scenario Stress Tester & Playground in Web UI."""
    st.markdown('<div class="ll-card-title">🧪 SCENARIO STRESS TESTER & ATTACK SIMULATOR</div>', unsafe_allow_html=True)
    st.caption("Live sandbox for compliance engineers to simulate synthetic financial crime injections and test real-time agent diagnostics.")

    col1, col2 = st.columns(2)
    with col1:
        sim_account = st.text_input("Target Test Account", value="ACC-SIM-ALPHA")
        inflow_amt = st.number_input("Injected Inflow Credit (INR)", min_value=100000.0, max_value=50000000.0, value=3500000.0, step=100000.0)
    with col2:
        mule_count = st.slider("Mule Recipient Count", min_value=2, max_value=15, value=5)
        window_mins = st.slider("Dispersal Time Window (Minutes)", min_value=5, max_value=120, value=30)

    if st.button("🚀 Inject Custom Topology & Execute Investigation", type="primary", use_container_width=True):
        with st.spinner("Injecting scenario transactions and executing real-time investigation..."):
            import subprocess
            cmd = f'python scripts/simulate_scenario.py --account {sim_account} --inflow {inflow_amt} --outflow-count {mule_count} --split-minutes {window_mins}'
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=str(ROOT))
            if proc.returncode == 0:
                st.success("✔ Scenario successfully injected and diagnosed by AI Investigator!")
                st.code(proc.stdout, language="text")
            else:
                st.error(f"Simulation encountered error: {proc.stderr}")


# === MAIN ===
def main():
    render_sidebar()
    render_main_area()



if __name__ == "__main__":
    main()
