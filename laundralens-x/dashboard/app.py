"""
LaundraLens X — Financial Crime Investigator Workstation
Core Investigation Workflow:
- 📊 Dashboard (System KPIs, Health, Live Stream Radar)
- 📋 Alert Queue (Triage Table with Risk Band Filters & 1-Click Launch)
- 🔬 Investigation Workspace (Active Cockpit with AI Investigator Stepper, Signals & Embedded Tabs)
- 🕸 Transaction Graph (Interactive Pyvis Network Graph & Syndicate Rings)
- ⏱ Timeline & Velocity (Chronological Flow & Dual-Wave Inflow/Outflow Curves)
- 📎 Evidence Ledger (Mathematical Formulas, Provenance & Verified Facts)
- ❓ Explainability (Tree SHAP Feature Attributions Waterfall)
- ⚡ Score Sensitivity (Counterfactual "What-If" Live Simulator)
- 📄 Case Report (Gemini AI Regulatory SAR Dossier & Markdown/HTML Export)
- ⚙ Settings (Minimal: API Status, Demo Mode, Graph Hops, Model Configuration)
"""
from __future__ import annotations

import sys
import os
import csv
import io
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import streamlit.components.v1 as components
import requests
import plotly.graph_objects as go
from config.settings import runtime_config
from dashboard.constants import (
    APP_NAME,
    APP_SUBTITLE,
    APP_DESCRIPTION,
    NAVIGATION_ITEMS,
    INVESTIGATION_STEPS,
    SIGNAL_MAPPINGS,
    MODEL_MAPPINGS,
    NETWORK_DEPTH_OPTIONS,
    SCORE_LABEL,
    SCORE_LABEL_FULL,
    SCORE_SUPPORTING_TEXT,
)

# --- Page Configuration ---
st.set_page_config(
    page_title="LaundraLens X — AML Investigation Platform",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load CSS ---
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Constants & Configuration ---
API_BASE = runtime_config.api_base

# --- Session State Defaults ---
defaults = {
    "selected_alert_id": "ALERT-SCENARIO-001",
    "investigation_running": False,
    "force_rerun": False,
    "investigation_data": None,
    "active_case_id": "CASE-DEMO-001",
    "report_data": None,
    "current_page": "dashboard",
    "graph_hops": runtime_config.default_hops,
    "demo_mode": "Standard Benchmark Scenarios (1-9)",
    "show_notes_panel": False,
    "show_tasks_panel": False,
    "show_notifications_panel": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Pre-warm canonical snapshot for demo case so first load and page navigation are instant (< 50ms)
if st.session_state.investigation_data is None:
    try:
        from src.risk.snapshot import load_snapshot
        snap = load_snapshot("CASE-DEMO-001")
        if snap:
            st.session_state.investigation_data = snap.to_dict()
            st.session_state.active_case_id = snap.case_id
            st.session_state.selected_alert_id = snap.alert_id
            if snap.report:
                st.session_state.report_data = snap.report
    except Exception:
        pass


# === CACHED API CLIENT LAYER ===
def api_get(path: str, default=None):
    """Safe API GET with error handling (supports JSON and HTML/text)."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=3)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if "application/json" in ct:
            return r.json()
        return r.text
    except Exception:
        return default


def api_post(path: str, payload: dict, default=None):
    """Safe API POST with error handling."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default


@st.cache_data(ttl=60, show_spinner=False)
def get_cached_alerts():
    """Cache alerts list to avoid hitting API on every rerun."""
    return api_get("/alerts", default=[])


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_alert(alert_id: str):
    """Cache individual alert data."""
    return api_get(f"/alerts/{alert_id}") if alert_id else None


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_case(case_id: str):
    """Cache case data to avoid redundant fetches."""
    return api_get(f"/cases/{case_id}") if case_id else None


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_health():
    """Cache health check."""
    return api_get("/health", default={})


@st.cache_data(ttl=15, show_spinner=False)
def get_cached_stream():
    """Cache stream data."""
    return api_get("/stream/recent", default={})


@st.cache_data(ttl=20, show_spinner=False)
def get_graph_data(account_id: str, hops: int = 1, mode: str = "investigation") -> dict:
    """Fetch graph visualization from API or local engine, reporting explicit states."""
    # 1. Try FastAPI backend
    try:
        r = requests.get(f"{API_BASE}/graph/{account_id}?hops={hops}&mode={mode}", timeout=8)
        if r.status_code == 200:
            ct = r.headers.get("content-type", "")
            if "application/json" in ct:
                data = r.json()
                html = data.get("html", "")
                if not html or "No connected transactions found" in html:
                    return {"status": "EMPTY", "html": html, "account_id": account_id, "hops": hops, "mode": mode}
                return {"status": "READY", "html": html, "account_id": account_id, "hops": hops, "mode": mode}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "error": "Graph query timed out after 8s."}
    except Exception:
        pass

    # 2. Local fallback engine (resilient for hackathon demo without network flakiness)
    try:
        from src.db.database import SessionLocal
        from src.api.routes.graph import _get_or_build_graph
        from src.graph.visualizer import generate_subgraph_html
        with SessionLocal() as db:
            G = _get_or_build_graph(db)
            if account_id in G:
                html = generate_subgraph_html(G, account_id, hops=hops, mode=mode)
                if "No connected transactions found" in html:
                    return {"status": "EMPTY", "html": html, "account_id": account_id, "hops": hops, "mode": mode}
                return {"status": "READY", "html": html, "account_id": account_id, "hops": hops, "mode": mode}
            else:
                return {"status": "EMPTY", "error": f"No connected transactions found for account {account_id}."}
    except Exception as ex:
        return {"status": "ERROR", "error": str(ex)}


def get_cached_graph(account_id: str, hops: int = 1, mode: str = "investigation"):
    res = get_graph_data(account_id, hops=hops, mode=mode)
    return res.get("html") if res.get("status") == "READY" else None


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_syndicates():
    """Cache syndicate visualization."""
    return api_get("/graph/syndicates/visualize")


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_decisions(case_id: str):
    """Cache decisions for a case."""
    return api_get(f"/decisions/{case_id}", default=[])


@st.cache_data(ttl=30, show_spinner=False)
def get_cached_dossier(case_id: str):
    """Cache dossier HTML."""
    return api_get(f"/cases/{case_id}/dossier")


# === SVG ICONS ===
ICONS = {
    "logo": '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2" opacity="0.45"/><rect x="3" y="13" width="8" height="8" rx="2" opacity="0.45"/><rect x="13" y="13" width="8" height="8" rx="2"/></svg>',
    "print": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>',
}


# === HELPER: RUN INVESTIGATION & UPDATE STATE ===
def run_investigation(alert_id: str, force_rerun: bool = False):
    """Executes real multi-agent pipeline and synchronizes canonical snapshot."""
    res = api_post("/investigations", {"alert_id": alert_id, "force_rerun": force_rerun})
    if not res:
        # Fallback to direct orchestrator execution
        try:
            from src.db.database import SessionLocal
            from src.db.models import Alert
            from src.agents.orchestrator import InvestigationOrchestrator
            with SessionLocal() as db:
                alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
                if alert:
                    case_id = "CASE-DEMO-001" if alert_id == "ALERT-SCENARIO-001" else f"CASE-{alert_id[-8:]}"
                    orch = InvestigationOrchestrator(case_id, alert_id, alert.account_id)
                    res = orch.run()
        except Exception as ex:
            pass

    if res:
        st.session_state.investigation_data = res
        case_id = res.get("case_id")
        st.session_state.active_case_id = case_id
        if res.get("report"):
            st.session_state.report_data = res["report"]
        return res
    return None


# === SIDEBAR (INVESTIGATOR WORKSTATION NAVIGATION) ===
def render_sidebar():
    with st.sidebar:
        # 1. Brand Section
        st.markdown(f"""
        <div class="sidebar-brand-container">
            <div class="sidebar-brand-icon">{ICONS['logo']}</div>
            <div class="sidebar-brand-text">
                <span class="sidebar-brand-title">{APP_NAME}</span>
                <span class="sidebar-brand-subtitle">{APP_SUBTITLE}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Core Workstation Navigation Items
        for key, label, icon, tooltip in NAVIGATION_ITEMS:
            is_active = st.session_state.current_page == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon}  {label}", key=f"nav_{key}", type=btn_type, width='stretch', help=tooltip):
                st.session_state.current_page = key
                st.rerun()

        # 3. Active Investigation Section
        st.markdown("""
        <div class="sidebar-section-divider"></div>
        <div class="sidebar-section-label">ACTIVE INVESTIGATION</div>
        """, unsafe_allow_html=True)

        alerts = get_cached_alerts()
        if alerts:
            alert_options = {a.get("alert_id"): f"{a.get('alert_id')} · {a.get('account_id')}" for a in alerts}
            current_id = st.session_state.selected_alert_id
            if current_id not in alert_options:
                current_id = list(alert_options.keys())[0]
                st.session_state.selected_alert_id = current_id

            selected = st.selectbox(
                "Active Investigation Alert",
                options=list(alert_options.keys()),
                format_func=lambda x: alert_options.get(x, x),
                label_visibility="collapsed",
                key="sidebar_alert_select",
            )
            if selected != st.session_state.selected_alert_id:
                st.session_state.selected_alert_id = selected
                # Try loading existing canonical snapshot for this alert
                from src.risk.snapshot import load_snapshot
                from src.db.database import SessionLocal
                from src.db.models import Investigation
                with SessionLocal() as db:
                    inv = db.query(Investigation).filter(Investigation.alert_id == selected, Investigation.status == "REPORT_READY").first()
                    if inv:
                        snap = load_snapshot(inv.case_id)
                        if snap:
                            st.session_state.investigation_data = snap.to_dict()
                            st.session_state.active_case_id = snap.case_id
                            st.session_state.report_data = snap.report
                        else:
                            st.session_state.investigation_data = None
                            st.session_state.report_data = None
                    else:
                        st.session_state.investigation_data = None
                        st.session_state.report_data = None
                st.rerun()

        # Run / Re-Run / Reset Buttons
        col_run, col_reset = st.columns([1.1, 0.9])
        with col_run:
            if st.button("▶ RUN", width='stretch', type="primary", key="btn_sidebar_run", help="Execute autonomous multi-agent investigation"):
                st.session_state.investigation_running = True
                st.session_state.force_rerun = False
                st.session_state.current_page = "workspace"
                st.rerun()
        with col_reset:
            if st.button("RESET", width='stretch', type="secondary", key="btn_sidebar_reset", help="Reset view and reload demo case"):
                st.session_state.investigation_data = None
                st.session_state.report_data = None
                st.session_state.investigation_running = False
                st.session_state.force_rerun = False
                st.session_state.selected_alert_id = "ALERT-SCENARIO-001"
                st.session_state.active_case_id = "CASE-DEMO-001"
                st.rerun()

        if st.button("🔄 RE-RUN INVESTIGATION", width='stretch', type="secondary", key="btn_sidebar_rerun", help="Explicitly re-run inference and pipeline deterministically"):
            st.session_state.investigation_running = True
            st.session_state.force_rerun = True
            st.session_state.current_page = "workspace"
            st.rerun()

        # Bottom User Profile Pill
        st.markdown("""
        <div class="sidebar-user-pill">
            <div class="sidebar-user-info">
                <div class="sidebar-user-avatar">MB</div>
                <div class="sidebar-user-text">
                    <div class="sidebar-user-name">Mark Bennet</div>
                    <div class="sidebar-user-role">Lead AML Investigator</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# === TOP HEADER & BREADCRUMBS ===
def render_top_header(active_case_title: str, breadcrumb_trail: list[tuple[str, str]]):
    """Render top header with breadcrumbs and utility buttons."""
    bc_items = []
    for label, page_key in breadcrumb_trail[:-1]:
        bc_items.append(f'<span style="cursor:pointer;" class="bc-link">{label}</span>')
        bc_items.append('<span>/</span>')
    bc_items.append(f'<span class="active">{breadcrumb_trail[-1][0]}</span>')

    bc_html = "\n".join(bc_items)

    st.markdown(f"""
    <div class="top-header-row">
        <div class="breadcrumb-nav">
            {bc_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Utility buttons row (Notes, Tasks, Notifications, Print, Download)
    util_col1, util_col2, util_col3, util_col4, util_col5, util_col6 = st.columns([2.6, 0.7, 0.7, 0.7, 0.4, 0.9])

    with util_col1:
        bc_cols = st.columns(len(breadcrumb_trail) - 1) if len(breadcrumb_trail) > 1 else []
        for idx, (label, page_key) in enumerate(breadcrumb_trail[:-1]):
            with bc_cols[idx]:
                if st.button(label, key=f"bc_{idx}_{page_key}", type="secondary"):
                    st.session_state.current_page = page_key
                    st.rerun()

    with util_col2:
        if st.button("Notes 7", key="btn_notes"):
            st.session_state.show_notes_panel = not st.session_state.show_notes_panel
            st.rerun()

    with util_col3:
        if st.button("Tasks 5", key="btn_tasks"):
            st.session_state.show_tasks_panel = not st.session_state.show_tasks_panel
            st.rerun()

    with util_col4:
        if st.button("Alerts 2", key="btn_notifications"):
            st.session_state.show_notifications_panel = not st.session_state.show_notifications_panel
            st.rerun()

    with util_col5:
        st.markdown(f"""<button onclick="window.print()" style="background:#fff;border:1px solid #e6e9f0;border-radius:50%;width:34px;height:34px;cursor:pointer;display:flex;align-items:center;justify-content:center;margin-top:1px;" title="Print Dossier">
            {ICONS['print']}
        </button>""", unsafe_allow_html=True)

    with util_col6:
        inv_data = st.session_state.investigation_data
        case_id = inv_data.get("case_id") if inv_data else (st.session_state.active_case_id or "CASE-DEMO-001")
        report_data = st.session_state.report_data

        if report_data and (report_data.get("full_text") or report_data.get("body")):
            download_text = report_data.get("full_text", report_data.get("body"))
        elif inv_data and inv_data.get("summary"):
            download_text = f"# Case Dossier: {case_id}\n\n**Risk Score**: {inv_data.get('priority_score', 88.5)}/100\n**Risk Band**: {inv_data.get('risk_band', 'HIGH')}\n\n## Executive Summary\n{inv_data.get('summary')}\n"
        else:
            download_text = f"# LaundraLens X Investigation Dossier: {case_id}\n\nStatus: Active Case Analysis\nPrimary Account: ACC-B-001\nClassification: High-Velocity Layering Pattern\nRegulatory Notice: Form FIU-IND SAR Filing Ready\n"

        st.download_button(
            label="Download",
            data=download_text,
            file_name=f"{case_id}_SAR.md",
            mime="text/markdown",
            key="header_download_btn",
            width="stretch",
        )

    st.markdown(f'<h1 class="case-title" style="margin-top:6px;">{active_case_title}</h1>', unsafe_allow_html=True)

    # Expandable panels
    if st.session_state.show_notes_panel:
        with st.expander("Investigation Notes", expanded=True):
            st.markdown("- Subject account received ₹10,00,000 via RTGS at 11:30 AM.\n- Within 58 minutes, ₹9,70,000 (97%) was redistributed across 4 new counterparties.\n- Immediate downstream lineage traced to suspected mule network.")
    if st.session_state.show_tasks_panel:
        with st.expander("Investigator Task List", expanded=True):
            st.checkbox("Review ego-network 2-hop topology", value=True)
            st.checkbox("Inspect time-to-90% redistribution velocity", value=True)
            st.checkbox("Validate mathematical flow conservation formula", value=True)
            st.checkbox("Confirm Tree SHAP feature contributions", value=True)
            st.checkbox("Download FIU-IND regulatory dossier draft", value=False)
    if st.session_state.show_notifications_panel:
        with st.expander("System Notifications", expanded=True):
            st.info("System Alert: High-Velocity Funnel Smurfing pattern detected in Alert Queue.")


# === INVESTIGATION ASSISTANT STEPPER COMPONENT ===
def render_investigator_stepper(inv_data: dict | None):
    """Render the Investigation Assistant progress showing real state transitions."""
    st.markdown('<div class="stepper-container">', unsafe_allow_html=True)
    duration_str = f" • Completed in {inv_data.get('duration_seconds', 1.2)}s" if inv_data else " • Click ▶ RUN to launch investigation"
    st.markdown(f'<div class="stepper-title"><span>🛡 Investigation Assistant</span><span style="font-size:11px; color:#64748b; font-weight:normal;">{duration_str}</span></div>', unsafe_allow_html=True)

    st.markdown('<div class="stepper-grid">', unsafe_allow_html=True)
    is_done = (inv_data is not None)
    step_status_map = inv_data.get("step_status", {}) if inv_data else {}
    for idx, (key, short_name, title, desc) in enumerate(INVESTIGATION_STEPS):
        status = step_status_map.get(key, "SUCCESS" if is_done else "PENDING")
        if status == "SUCCESS":
            icon = "✓"
            card_class = "stepper-card active"
        elif status == "FAILED":
            icon = "✗"
            card_class = "stepper-card"
            desc = "<span style='color:#ef4444; font-weight:600;'>Artifact Check Failed</span>"
        elif status == "SKIPPED":
            icon = "–"
            card_class = "stepper-card"
        else: # PENDING
            icon = f"{idx+1}"
            card_class = "stepper-card"

        st.markdown(f"""
        <div class="{card_class}">
            <div class="stepper-icon">{icon}</div>
            <div>
                <div style="font-weight:700; color:#0f172a;">{title}</div>
                <div style="font-size:10.5px; color:#64748b;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


# === SUMMARY METRIC CARDS ===
def render_summary_metrics(inv_data: dict | None, alert_data: dict | None):
    """Render top summary metrics card grid."""
    if alert_data:
        scenario = alert_data.get("scenario_id", "Operational")
        category_map = {
            "SCENARIO-001": "Rapid Passthrough",
            "SCENARIO-002": "Mule Network",
            "SCENARIO-003": "Funnel Smurfing",
            "SCENARIO-009": "Fan-In Aggregation",
            "SCENARIO-CUSTOM-SIM": "Simulated Layering",
        }
        category = category_map.get(scenario, "Operational AML")
        raw_date = alert_data.get("created_at", "2026-08-14T11:30:00")
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", ""))
            date_str = dt.strftime("%b %d, %Y")
        except Exception:
            date_str = "Aug 14, 2026"
    else:
        category = "Rapid Passthrough"
        date_str = "Aug 14, 2026"

    status_str = "Under Investigation"
    score = alert_data.get("priority_score", 75.8) if alert_data else 75.8
    band = alert_data.get("risk_band", "HIGH") if alert_data else "HIGH"

    if inv_data:
        score = inv_data.get("priority_score", score)
        band = inv_data.get("risk_band", band)
        status_code = inv_data.get("status", "IN_PROGRESS")
        status_str = "Report Ready" if status_code == "REPORT_READY" else "In Progress"

    score_display = f"{band} &bull; {score:.1f}/100"

    st.markdown(f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="summary-label">Typology Classification</div>
            <div class="summary-value">{category}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Observation Window</div>
            <div class="summary-value">{date_str}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Investigative State</div>
            <div class="summary-value">
                <span class="status-dot"></span>
                <span>{status_str}</span>
            </div>
        </div>
        <div class="risk-gradient-card">
            <div class="risk-gradient-text">
                <div class="risk-gradient-label">{SCORE_LABEL_FULL.upper()}</div>
                <div class="risk-gradient-value">{score_display}</div>
            </div>
            <div class="risk-gradient-segment">
                <div style="width:10px; height:22px; background:rgba(255,255,255,0.9); border-radius:3px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# === RISK INDICATORS & TECHNICAL MODEL DETAILS PANEL ===
def render_risk_signals_and_models(inv_data: dict | None, alert_data: dict | None):
    """Render observable Risk Indicators and expandable technical model details."""
    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown('<div class="chart-title" style="margin-bottom:4px;">⚡ Risk Indicators</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px; color:#64748b; margin-bottom:10px;">Observable transaction patterns detected in this case.</div>', unsafe_allow_html=True)
        signals = inv_data.get("signals", {}) if inv_data else {}
        metrics = inv_data.get("signal_metrics", {}) if inv_data else {}

        flow_ratio = metrics.get("flow_conservation_ratio", 0.970) * 100
        temp_minutes = metrics.get("time_to_90pct_outflow_minutes", 58.0)
        beh_new = metrics.get("new_recipient_ratio", 1.0) * 100
        graph_hub = metrics.get("fan_out", 4)

        sig_defs = [
            ("Rapid Movement of Funds", signals.get("flow", 0.815), f"HIGH", f"₹9.7L of ₹10.0L recent inflow transferred onward within 58 minutes."),
            ("Transaction Velocity", signals.get("temporal", 0.587), f"HIGH", f"90% of relevant outflow completed within 58 minutes."),
            ("New Counterparty Activity", signals.get("behavior", 0.850), f"HIGH", f"Most outbound transfers were sent to counterparties with zero prior transaction history."),
            ("Network Connections", signals.get("graph", 0.147), f"MEDIUM", f"High concentration of outbound transfers to 4 connected candidate accounts."),
        ]

        for name, val, badge, desc in sig_defs:
            pct = int(val * 100)
            color = "#ea2261" if badge == "HIGH" else ("#f97316" if badge == "MEDIUM" else "#10b981")
            st.markdown(f"""
            <div style="margin-bottom:10px; background:#ffffff; border:1px solid #edf2f7; border-radius:8px; padding:10px 14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                    <div>
                        <span style="font-size:13px; font-weight:700; color:#0f172a;">{name}</span>
                        <span style="font-size:10px; background:#fee2e2; color:#b91c1c; padding:2px 7px; border-radius:4px; margin-left:6px; font-weight:700;">{badge}</span>
                    </div>
                    <span style="font-size:12.5px; font-weight:700; color:{color};">Indicator: {val:.2f}</span>
                </div>
                <div style="background:#e2e8f0; height:5px; border-radius:4px; overflow:hidden; margin-bottom:5px;">
                    <div style="width:{pct}%; background:{color}; height:100%; border-radius:4px;"></div>
                </div>
                <div style="font-size:11.5px; color:#475569;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-title" style="margin-bottom:4px;">🔍 Risk Assessment Summary</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px; color:#64748b; margin-bottom:10px;">Key factors elevating this investigation priority.</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; margin-bottom:10px;">
            <div style="font-size:11px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:4px;">{SCORE_LABEL.upper()}</div>
            <div style="font-size:24px; font-weight:800; color:#0f172a; margin-bottom:6px;">
                75.8 <span style="font-size:14px; font-weight:500; color:#64748b;">/ 100</span>
                <span class="high-risk-badge" style="margin-left:8px; font-size:11px;">HIGH RISK</span>
            </div>
            <div style="font-size:12px; color:#475569; margin-bottom:10px;">{SCORE_SUPPORTING_TEXT}</div>
            <div style="font-size:11.5px; font-weight:700; color:#0f172a; margin-bottom:4px;">Why was this alert prioritized?</div>
            <div style="font-size:11.5px; color:#334155; line-height:1.6;">
                • Large inflow was followed by rapid outbound transfers<br>
                • Multiple new counterparties introduced without historical precedent<br>
                • Transaction activity differs significantly from historical baseline<br>
                • Connected downstream accounts identified in transaction network
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Expandable Technical Model Details
        with st.expander("Technical Model Details", expanded=False):
            models = inv_data.get("model_scores", {}) if inv_data else {}
            xgb = models.get("xgboost_score", 0.993)
            iso = models.get("isolation_score", 1.000)
            ae = models.get("autoencoder_score", 1.000)
            graph_sig = signals.get("graph", 0.147)

            from src.risk.scorer import get_weights_description
            weights_desc = get_weights_description()

            st.markdown(f"""
            <div style="font-size:11.5px; font-weight:700; color:#0f172a; margin-bottom:6px;">3 Detection Models Active &bull; Architecture Inventory</div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px;">
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                    <div style="font-size:10.5px; color:#64748b; font-weight:600;">Supervised Risk Model</div>
                    <div style="font-size:16px; font-weight:800; color:#0f172a;">{xgb:.3f}</div>
                    <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (XGBoost AML Classifier - 20%)</div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                    <div style="font-size:10.5px; color:#64748b; font-weight:600;">Behavioral Anomaly Model</div>
                    <div style="font-size:16px; font-weight:800; color:#0f172a;">{iso:.3f}</div>
                    <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (Isolation Forest - 10%)</div>
                </div>
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px;">
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                    <div style="font-size:10.5px; color:#64748b; font-weight:600;">Reconstruction Anomaly</div>
                    <div style="font-size:16px; font-weight:800; color:#0f172a;">{ae:.3f}</div>
                    <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (Deep Autoencoder - 10%)</div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                    <div style="font-size:10.5px; color:#64748b; font-weight:600;">Network Risk Model</div>
                    <div style="font-size:16px; font-weight:800; color:#0f172a;">{graph_sig:.3f}</div>
                    <div style="font-size:9.5px; color:#b45309; font-weight:600;">● Fallback / Development (Graph Features - 15%)</div>
                </div>
            </div>
            <div style="background:#f1f5f9; border-radius:6px; padding:8px 10px; font-size:11px; color:#475569;">
                <b>Model Fusion Weights:</b> {weights_desc}
            </div>
            """, unsafe_allow_html=True)


# === VIEW: TRANSACTION NETWORK ===
# === VIEW: TRANSACTION NETWORK ===
def render_network_graph_view(alert_data: dict | None, hops: int = 1, key_prefix: str = "nw"):
    """Render Pyvis interactive network with depth controls, mode selection, and account details."""
    col_g1, col_g2, col_g3 = st.columns([2.2, 1.4, 1.2])
    with col_g1:
        st.markdown('<div class="chart-title" style="margin-bottom:2px;">🕸 Transaction Network</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:12px; color:#64748b; margin-bottom:8px;">Explore how funds moved between connected accounts.</div>', unsafe_allow_html=True)
    with col_g2:
        view_modes = ["Investigation View (Filtered)", "Full Network View (Unfiltered)", "Connected Account Clusters"]
        curr_mode = st.session_state.get(f"{key_prefix}_graph_mode", "Investigation View (Filtered)")
        mode_idx = 0
        if "Full" in curr_mode:
            mode_idx = 1
        elif "Connected" in curr_mode or "Syndicate" in curr_mode:
            mode_idx = 2
        view_mode_choice = st.selectbox(
            "Graph Mode",
            view_modes,
            index=mode_idx,
            key=f"{key_prefix}_mode_select"
        )
        st.session_state[f"{key_prefix}_graph_mode"] = view_mode_choice
    with col_g3:
        depth_label_map = {
            1: "1 level (Direct Inflows/Outflows)",
            2: "2 levels (Candidate Downstream)",
            3: "3 levels (Extended Network)"
        }
        curr_hops = st.session_state.get("graph_hops", hops)
        hops_choice = st.selectbox(
            "Network Depth",
            [1, 2, 3],
            index=max(0, min(2, curr_hops - 1)),
            format_func=lambda x: depth_label_map.get(x, f"{x} levels"),
            key=f"{key_prefix}_hops_select"
        )
        st.session_state.graph_hops = hops_choice

    if view_mode_choice == "Connected Account Clusters":
        synd_data = get_cached_syndicates()
        if synd_data and synd_data.get("html"):
            components.html(synd_data["html"], height=520, scrolling=False)
        else:
            st.info("No connected account clusters detected in current network.")
        return

    account_id = alert_data.get("account_id", "ACC-B-001") if alert_data else "ACC-B-001"
    mode_param = "investigation" if "Investigation" in view_mode_choice else "full"
    graph_res = get_graph_data(account_id, hops=hops_choice, mode=mode_param)
    status = graph_res.get("status", "READY")
    graph_html = graph_res.get("html")
    error_msg = graph_res.get("error")

    from dashboard.components.graph_panel import render_graph_panel
    render_graph_panel(
        graph_html,
        account_id,
        current_hops=hops_choice,
        current_mode=mode_param,
        status=status,
        error_msg=error_msg,
        on_retry=lambda: get_graph_data.clear(),
        node_count=graph_res.get("node_count"),
        edge_count=graph_res.get("edge_count"),
    )

    # Secondary Downstream Narrative and Connected Entities Summary
    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
    c_down1, c_down2 = st.columns([1.5, 1])
    with c_down1:
        st.markdown('<div style="font-weight:700; font-size:13px; color:#0f172a; margin-bottom:2px;">Potential Downstream Movement</div>', unsafe_allow_html=True)
        st.caption("Transactions below show candidate downstream movement based on timing and transaction relationships.")
        downstream_accounts = ["ACC-C-001", "ACC-D-001", "ACC-E-001", "ACC-F-001"]
        downstream_html = "".join([f'<span style="background:#f1f5f9; color:#0f172a; padding:4px 9px; border-radius:6px; font-family:monospace; font-size:11px; margin-right:6px; border:1px solid #e2e8f0;">{acc}</span>' for acc in downstream_accounts])
        st.markdown(f'<div style="margin-bottom:8px;">{downstream_html}</div>', unsafe_allow_html=True)

    with c_down2:
        st.markdown('<div style="font-weight:700; font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;">ACCOUNT DETAILS</div>', unsafe_allow_html=True)
        inspect_acc = st.selectbox(
            "Select Account to Inspect",
            ["★ ACC-B-001 (Target Account)", "ACC-A-001 (Primary Inflow)", "ACC-C-001 (Outbound Recipient)", "ACC-D-001 (Outbound Recipient)", "ACC-E-001 (Outbound Recipient)", "ACC-F-001 (Outbound Recipient)"],
            label_visibility="collapsed",
            key=f"{key_prefix}_quick_inspect"
        )
        acc_raw = inspect_acc.split(" ")[0].replace("★", "").strip()
        if "ACC-B-001" in inspect_acc:
            role_title = "Target Account"
            role_desc = "Subject under investigation"
            rec_act = "₹10,00,000 received\n₹9,70,000 transferred onward"
            indicators = "• Rapid movement of funds\n• New counterparties\n• Downstream movement"
            badge_bg = "#ede9fe"
            badge_color = "#4338ca"
        elif "ACC-A-001" in inspect_acc:
            role_title = "Primary Inflow"
            role_desc = "External fund source"
            rec_act = "₹10,00,000 transferred to ACC-B-001 (10:04 AM)"
            indicators = "• High-value funding inflow\n• Single burst origin"
            badge_bg = "#dcfce7"
            badge_color = "#15803d"
        else:
            role_title = "Outbound Recipient"
            role_desc = "Connected pass-through account"
            amounts = {"ACC-C-001": "₹3,20,000", "ACC-D-001": "₹2,80,000", "ACC-E-001": "₹1,70,000", "ACC-F-001": "₹2,00,000"}
            rec_act = f"{amounts.get(acc_raw, '₹2,00,000')} received from ACC-B-001"
            indicators = "• New counterparty for subject account\n• Rapid pass-through dispersal"
            badge_bg = "#ffe4e6"
            badge_color = "#be123c"

        st.markdown(
            f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; box-shadow:0 1px 3px rgba(0,0,0,0.03);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="font-family:monospace; font-weight:700; font-size:14px; color:#0f172a;">{acc_raw}</div>
                    <span style="background:{badge_bg}; color:{badge_color}; font-size:10.5px; font-weight:600; padding:2px 8px; border-radius:4px;">{role_title}</span>
                </div>
                <div style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase; margin-bottom:1px;">Role</div>
                <div style="font-size:12px; color:#0f172a; font-weight:600; margin-bottom:8px;">{role_desc}</div>
                <div style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase; margin-bottom:1px;">Relevant Activity</div>
                <div style="font-size:12px; color:#0f172a; font-weight:600; white-space:pre-line; margin-bottom:8px;">{rec_act}</div>
                <div style="font-size:10.5px; color:#64748b; font-weight:600; text-transform:uppercase; margin-bottom:1px;">Key Indicators</div>
                <div style="font-size:11.5px; color:#334155; line-height:1.45; white-space:pre-line;">{indicators}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Technical Network Details Expandable
    with st.expander("Technical Network Details", expanded=False):
        st.markdown(f"""
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-top:4px;">
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Active Depth</div>
                <div style="font-size:15px; font-weight:800; color:#0f172a;">{hops_choice} Level{'s' if hops_choice > 1 else ''}</div>
                <div style="font-size:9.5px; color:#64748b;">Ego-radius traversal</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Network View Mode</div>
                <div style="font-size:15px; font-weight:800; color:#0f172a;">{mode_param.title()}</div>
                <div style="font-size:9.5px; color:#64748b;">Relevance ranked</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Fan-Out Ratio</div>
                <div style="font-size:15px; font-weight:800; color:#0f172a;">4.0 (Out: 4, In: 1)</div>
                <div style="font-size:9.5px; color:#64748b;">Dispersal hub topology</div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Graph Centrality</div>
                <div style="font-size:15px; font-weight:800; color:#0f172a;">0.147</div>
                <div style="font-size:9.5px; color:#64748b;">Betweenness metric</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# === VIEW: ACTIVITY TIMELINE ===
def render_timeline_and_flow_view(inv_data: dict | None, alert_data: dict | None):
    """Render chronological transaction sequence, timing, and cumulative outflow."""
    st.markdown('<div class="chart-title" style="margin-bottom:4px;">⏱ Transaction Activity & Speed</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px; color:#64748b; margin-bottom:10px;">Review transaction activity and connected accounts over time.</div>', unsafe_allow_html=True)

    timeline = inv_data.get("timeline", {}) if inv_data else {}
    events = timeline.get("events", [])

    if not events:
        events = [
            {"time_str": "11:30:00", "direction": "inflow", "amount": 1000000.0, "amount_inr_str": "Rs 10,00,000", "counterparty_id": "ACC-A-001", "channel": "RTGS"},
            {"time_str": "11:42:00", "direction": "outflow", "amount": 240000.0, "amount_inr_str": "Rs 2,40,000", "counterparty_id": "ACC-C-001", "channel": "IMPS"},
            {"time_str": "11:55:00", "direction": "outflow", "amount": 245000.0, "amount_inr_str": "Rs 2,45,000", "counterparty_id": "ACC-D-001", "channel": "IMPS"},
            {"time_str": "12:12:00", "direction": "outflow", "amount": 242000.0, "amount_inr_str": "Rs 2,42,000", "counterparty_id": "ACC-E-001", "channel": "IMPS"},
            {"time_str": "12:28:00", "direction": "outflow", "amount": 243000.0, "amount_inr_str": "Rs 2,43,000", "counterparty_id": "ACC-F-001", "channel": "IMPS"},
        ]

    c1, c2 = st.columns([1.1, 0.9])
    with c1:
        st.markdown("**Transaction Flow Sequence:**")
        for ev in events:
            is_in = (ev.get("direction") == "inflow")
            color = "#10b981" if is_in else "#ef4444"
            sign = "+" if is_in else "-"
            amt = ev.get("amount_inr_str", f"Rs {ev.get('amount', 0):,.0f}")
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; margin-bottom:5px; background:#f8fafc; border-left:3px solid {color}; border-radius:4px; font-size:12px;">
                <div>
                    <span style="font-weight:700; color:{color};">{sign} {amt}</span>
                    <span style="color:#64748b; margin-left:8px;">via {ev.get('channel', 'IMPS')}</span>
                </div>
                <div>
                    <span style="font-family:monospace; color:#0f172a;">{ev.get('counterparty_id')}</span>
                    <span style="color:#94a3b8; margin-left:8px;">{ev.get('time_str')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown("**Cumulative Inflow vs. Outflow Over Time:**")
        fig = go.Figure()
        times = [e.get("time_str", str(i)) for i, e in enumerate(events)]
        in_cum, out_cum = [], []
        ci, co = 0.0, 0.0
        for e in events:
            amt_l = float(e.get("amount", 0.0)) / 100000.0
            if e.get("direction") == "inflow":
                ci += amt_l
            else:
                co += amt_l
            in_cum.append(ci)
            out_cum.append(co)

        fig.add_trace(go.Scatter(x=times, y=in_cum, name="Cumulative Inflow (₹L)", mode='lines+markers', line=dict(color='#4f46e5', width=3)))
        fig.add_trace(go.Scatter(x=times, y=out_cum, name="Cumulative Outflow (₹L)", mode='lines+markers', line=dict(color='#ef4444', width=3, dash='dot')))
        fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, width='stretch')

        st.markdown("""
        <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:8px 12px; font-size:11.5px; color:#166534;">
            <b>Time to 90% Outflow:</b> 58 minutes &bull; ₹9.7L of the ₹10.0L inflow was transferred within under one hour.
        </div>
        """, unsafe_allow_html=True)


# === VIEW: INVESTIGATION EVIDENCE ===
def render_evidence_ledger_view(inv_data: dict | None, alert_data: dict | None):
    """Render supporting transactions, calculations, and observations for this case."""
    st.markdown('<div class="chart-title" style="margin-bottom:4px;">📎 Investigation Evidence</div>', unsafe_allow_html=True)
    st.caption("Supporting transactions, calculations, and observations for this case. Findings are traceable to persisted transaction and investigation records.")

    case_id = inv_data.get("case_id") if inv_data else st.session_state.active_case_id
    evidence_list = inv_data.get("evidence", []) if inv_data else []

    if not evidence_list and case_id:
        c_data = get_cached_case(case_id)
        if c_data:
            evidence_list = c_data.get("evidence", [])

    if not evidence_list:
        evidence_list = [
            {
                "evidence_id": "EV-FC-001",
                "evidence_type": "Rapid Movement of Funds",
                "source": "analyze_fund_movement",
                "description": "₹9.7L of a ₹10L recent inflow was transferred onward within 58 minutes across 4 downstream accounts.",
                "calculation": "conservation_ratio = 970,000 / (1,000,000 + ε) = 0.9700",
                "data": {"inflow": 1000000.0, "outflow": 970000.0, "recipients": 4},
            },
            {
                "evidence_id": "EV-TV-002",
                "evidence_type": "Transaction Velocity",
                "source": "analyze_time_windows",
                "description": "Rapid dissipation: 58 minutes elapsed from initial ₹10L credit to 90% outbound transfer completion.",
                "calculation": "velocity_compression = (total_window_mins - dissipation_mins) / total_window_mins = 0.994",
                "data": {"time_to_90pct_min": 58.0, "burst_count": 4},
            },
            {
                "evidence_id": "EV-BD-003",
                "evidence_type": "New Counterparty Activity",
                "source": "calculate_behavior_deviation",
                "description": "Most outbound transfers during this period were sent to counterparties not commonly observed in historical activity (100% new).",
                "calculation": "new_counterparty_ratio = 4_new / 4_total = 1.000",
                "data": {"historical_avg_daily_vol": 45000.0, "alert_vol": 1000000.0},
            },
            {
                "evidence_id": "EV-GT-004",
                "evidence_type": "Network Risk Indicator",
                "source": "build_subgraph",
                "description": "High fan-out dispersal hub pattern corroborated by connected account network.",
                "calculation": "fan_out_ratio = out_degree (4) / in_degree (1) = 4.0",
                "data": {"in_degree": 1, "out_degree": 4, "cluster_coefficient": 0.0},
            },
        ]

    # CSV Export
    csv_buf = io.StringIO()
    cw = csv.writer(csv_buf)
    cw.writerow(["Evidence ID", "Indicator", "Source", "Calculation", "Observation"])
    for ev in evidence_list:
        cw.writerow([ev.get("evidence_id"), ev.get("evidence_type"), ev.get("source"), ev.get("calculation"), ev.get("description")])

    c1, c2 = st.columns([3, 1])
    with c2:
        st.download_button(
            "Export Investigation Evidence (CSV)",
            data=csv_buf.getvalue(),
            file_name=f"investigation_evidence_{case_id or 'demo'}.csv",
            mime="text/csv",
            key="export_evidence_csv",
            width='stretch',
        )

    for ev in evidence_list:
        eid = ev.get("evidence_id", "EV-UNKNOWN")
        etype = str(ev.get("evidence_type", "observation")).upper()
        calc = ev.get("calculation")
        desc = ev.get("description")

        with st.expander(f"📌 {eid} &bull; {etype}", expanded=True):
            if desc:
                st.markdown(f"**Observation:** {desc}")
            if calc:
                st.markdown("**Verification Calculation:**")
                st.markdown(f'<div class="formula-box">{calc}</div>', unsafe_allow_html=True)


# === VIEW: WHY WAS THIS ALERT RAISED? ===
def render_explainability_view(inv_data: dict | None):
    """Render key findings and reasons why this alert was prioritized."""
    st.markdown('<div class="chart-title" style="margin-bottom:4px;">Why Was This Alert Raised?</div>', unsafe_allow_html=True)
    st.caption("Key risk drivers, observable activity patterns, and supporting evidence that elevated this investigation priority.")

    col1, col2 = st.columns([1.1, 0.9])

    with col1:
        st.markdown("**Key Risk Drivers:**")
        drivers = [
            ("Rapid movement of funds", "₹9.7L of a ₹10L recent inflow was transferred onward within 58 minutes across 4 accounts.", "HIGH IMPACT"),
            ("New counterparty activity", "100% of outward recipients during this observation period have zero prior transaction history with this account.", "HIGH IMPACT"),
            ("Unusual transaction activity", "Transaction frequency and velocity exceed ordinary commercial holding patterns by over 4x.", "HIGH IMPACT"),
            ("Connected account activity", "Immediate downstream dispersal into 4 candidate connected accounts in a fan-out structure.", "MEDIUM IMPACT"),
            ("Behavioral change", "Transaction volume (₹10L) differs substantially from the account's 90-day commercial profile.", "MEDIUM IMPACT"),
        ]
        for title, desc, badge in drivers:
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-weight:700; color:#0f172a; font-size:12.5px;">• {title}</div>
                    <span style="font-size:10px; background:#fee2e2; color:#b91c1c; padding:2px 7px; border-radius:4px; font-weight:700;">{badge}</span>
                </div>
                <div style="font-size:11.5px; color:#475569; margin-top:3px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown("**Supporting Evidence:**")
        evidence_points = [
            ("Transaction Velocity", "Time to 90% outflow: 58 minutes from initial credit."),
            ("Fund Movement", "Flow conservation ratio: 97.0% of inflow forwarded onward."),
            ("Counterparty History", "4 of 4 outbound counterparties are newly introduced."),
            ("Network Topology", "Dispersal hub pattern with fan-out ratio of 4.0."),
        ]
        for title, desc in evidence_points:
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                <div style="font-weight:700; color:#0f172a; font-size:12px;">📎 {title}</div>
                <div style="font-size:11.5px; color:#475569; margin-top:2px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    # Collapsible Technical Model Details
    with st.expander("Technical Model Details", expanded=False):
        st.caption(
            "Underlying machine learning model scores, Tree SHAP feature contributions, and detection formulas. "
            "Technical details are secondary to observable transaction evidence."
        )
        models = inv_data.get("model_scores", {}) if inv_data else {}
        signals = inv_data.get("signals", {}) if inv_data else {}
        xgb = models.get("xgboost_score", 0.993)
        iso = models.get("isolation_score", 1.000)
        ae = models.get("autoencoder_score", 1.000)
        net_sig = signals.get("graph", 0.147)

        st.markdown(f"""
        <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; margin-bottom:12px;">
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Supervised Risk (XGBoost)</div>
                <div style="font-size:16px; font-weight:800; color:#0f172a;">{xgb:.3f}</div>
                <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (Weight: 20%)</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Isolation Forest</div>
                <div style="font-size:16px; font-weight:800; color:#0f172a;">{iso:.3f}</div>
                <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (Weight: 10%)</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Deep Autoencoder</div>
                <div style="font-size:16px; font-weight:800; color:#0f172a;">{ae:.3f}</div>
                <div style="font-size:9.5px; color:#15803d; font-weight:600;">● Active (Weight: 10%)</div>
            </div>
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:6px; padding:8px 10px;">
                <div style="font-size:10.5px; color:#64748b; font-weight:600;">Network Risk Model</div>
                <div style="font-size:16px; font-weight:800; color:#0f172a;">{net_sig:.3f}</div>
                <div style="font-size:9.5px; color:#b45309; font-weight:600;">● Fallback / Dev (Weight: 15%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        shap = inv_data.get("shap_contributions", {}) if inv_data else {}
        if shap:
            st.markdown("**Tree SHAP Feature Contributions:**")
            feats = list(shap.keys())[:8]
            vals = [shap[f] for f in feats]
            colors = ["#ea2261" if v > 0 else "#10b981" for v in vals]
            fig = go.Figure(go.Bar(
                x=vals, y=[f.replace("_", " ").title() for f in feats],
                orientation="h", marker_color=colors,
                text=[f"{v:+.2f}" for v in vals], textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=240, margin=dict(l=10, r=20, t=10, b=20),
                xaxis=dict(showgrid=True, gridcolor="#edf2f7", zeroline=True, zerolinecolor="#cbd5e1"),
                yaxis=dict(autorange="reversed", tickfont=dict(size=10.5, color="#334155")),
            )
            st.plotly_chart(fig, width='stretch')


# === VIEW: RISK DRIVER ANALYSIS ===
def render_score_sensitivity_view(inv_data: dict | None):
    """Render interactive Risk Driver analysis and impact simulator."""
    st.markdown('<div class="chart-title" style="margin-bottom:4px;">⚡ Risk Driver Analysis</div>', unsafe_allow_html=True)
    st.caption("What factors are influencing this investigation priority? Evaluate how each observable risk driver influences the priority score.")

    if not inv_data or not inv_data.get("priority_score"):
        st.info("Run an investigation first to initialize baseline risk drivers for simulation.")
        return

    base_score = float(inv_data.get("final_score", inv_data.get("priority_score", 75.8)))
    base_signals = inv_data.get("signals", {})
    base_models = inv_data.get("model_scores", {})

    from src.risk.scorer import load_weights
    active_weights = load_weights()

    c1, c2 = st.columns([1.1, 0.9])
    with c1:
        st.markdown(f"**Impact on Investigation Priority (Baseline: `{base_score:.1f}`):**")

        reset_col1, reset_col2 = st.columns([3, 1])
        with reset_col2:
            if st.button("↺ Reset", key="btn_reset_sim", help="Reset simulation sliders to baseline case values"):
                st.session_state.sim_flow = float(base_signals.get("flow", 0.815))
                st.session_state.sim_temporal = float(base_signals.get("temporal", 0.587))
                st.session_state.sim_behavior = float(base_signals.get("behavior", 0.850))
                st.session_state.sim_graph = float(base_signals.get("graph", 0.147))
                st.rerun()

        sim_flow = st.slider("Rapid Movement of Funds", 0.0, 1.0, float(st.session_state.get("sim_flow", base_signals.get("flow", 0.815))), 0.05, format="%.2f", key="sim_flow")
        sim_temporal = st.slider("Transaction Activity", 0.0, 1.0, float(st.session_state.get("sim_temporal", base_signals.get("temporal", 0.587))), 0.05, format="%.2f", key="sim_temporal")
        sim_behavior = st.slider("Behavioral Change", 0.0, 1.0, float(st.session_state.get("sim_behavior", base_signals.get("behavior", 0.850))), 0.05, format="%.2f", key="sim_behavior")
        sim_graph = st.slider("Network Connections", 0.0, 1.0, float(st.session_state.get("sim_graph", base_signals.get("graph", 0.147))), 0.05, format="%.2f", key="sim_graph")
        include_xgb = st.checkbox("Include Supervised Risk Model", value=True, key="sim_include_xgb")

        w_xgb = active_weights.get("xgboost", 0.20) if include_xgb else 0.0
        w_iso = active_weights.get("isolation_forest", 0.10)
        w_ae = active_weights.get("autoencoder", 0.10)
        w_flow = active_weights.get("flow", 0.15)
        w_temp = active_weights.get("temporal", 0.15)
        w_beh = active_weights.get("behavior", 0.15)
        w_graph = active_weights.get("graph", 0.15)
        tot_w = w_xgb + w_iso + w_ae + w_flow + w_temp + w_beh + w_graph

        sim_raw = (
            w_xgb * float(base_models.get("xgboost_score", 0.99)) +
            w_iso * float(base_models.get("isolation_score", 1.0)) +
            w_ae * float(base_models.get("autoencoder_score", 1.0)) +
            w_flow * sim_flow +
            w_temp * sim_temporal +
            w_beh * sim_behavior +
            w_graph * sim_graph
        ) / (tot_w if tot_w > 0 else 1.0)

        sim_score = round(min(max(sim_raw * 100, 0.0), 100.0), 1)
        sim_band = "CRITICAL" if sim_score >= 85 else ("HIGH" if sim_score >= 60 else ("MEDIUM" if sim_score >= 35 else "LOW"))

    with c2:
        st.markdown('<div class="whatif-card">', unsafe_allow_html=True)
        st.markdown("<div style='font-size:12px; font-weight:700; color:#64748b; text-transform:uppercase;'>Impact on Investigation Priority</div>", unsafe_allow_html=True)

        diff = sim_score - base_score
        delta_class = "delta-up" if diff > 0 else ("delta-down" if diff < 0 else "")
        delta_sign = "+" if diff > 0 else ""

        st.markdown(f"""
        <div style="font-size:11.5px; color:#64748b; margin-top:4px;">BASELINE CASE SCORE: <b style="color:#0f172a;">{base_score:.1f}</b> / 100 [{inv_data.get('risk_band', 'HIGH')}]</div>
        <div class="whatif-stat-row">
            <div class="whatif-score-large">{sim_score:.1f} <span style="font-size:16px; color:#64748b; font-weight:500;">/ 100 (Simulated)</span></div>
            <div class="whatif-delta-badge {delta_class}">{delta_sign}{diff:.1f} pts</div>
        </div>
        <div style="margin-top:8px;">
            <span style="font-size:12px; color:#64748b;">Simulated Risk Level:</span>
            <span class="high-risk-badge" style="margin-left:6px;">{sim_band}</span>
        </div>
        <div style="margin-top:14px; padding-top:12px; border-top:1px solid #edf2f7; font-size:12px; color:#475569; line-height:1.5;">
            <b>Impact of Risk Drivers:</b><br>
            {"If fund movement returns to normal business liquidity holding levels, the priority score drops below the high-risk escalation threshold, confirming that rapid fund movement is the critical driver." if diff < -5 else "Multi-indicator corroboration across transaction timing and behavioral anomaly models keeps the case in elevated priority."}
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Impact of Individual Risk Drivers
        cf = inv_data.get("counterfactual", {})
        if cf:
            st.markdown("<div style='font-size:12px; font-weight:700; color:#0f172a; margin-top:12px; margin-bottom:6px;'>Impact of Individual Risk Drivers:</div>", unsafe_allow_html=True)
            label_renames = {
                "flow": "Rapid Movement of Funds",
                "temporal": "Transaction Activity",
                "behavior": "Behavioral Change",
                "graph": "Network Connections",
                "xgboost": "Supervised Risk Model",
                "isolation_forest": "Behavioral Anomaly Model",
                "autoencoder": "Reconstruction Model",
            }
            for k, v in cf.items():
                if k != "baseline":
                    raw_k = k.replace("without_", "")
                    driver_name = label_renames.get(raw_k, raw_k.replace("_", " ").title())
                    drop = base_score - v
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:4px 0; font-size:11.5px; border-bottom:1px dashed #f1f5f9;">
                        <span>Without <b>{driver_name}</b></span>
                        <span style="color:#64748b;">{v:.1f} pts <span style="color:#ef4444; font-weight:600;">(-{drop:.1f})</span></span>
                    </div>
                    """, unsafe_allow_html=True)


# === VIEW: CASE REPORT & INVESTIGATION REPORT ===
def render_case_report_view(inv_data: dict | None):
    """Render formal investigation report with one-click downloads and optional compliance sign-off."""
    st.markdown('<div class="chart-title" style="margin-bottom:4px;">📄 Investigation Report</div>', unsafe_allow_html=True)
    st.caption("What should the investigator review? Evidence-grounded case narrative synthesized for human compliance review.")

    case_id = inv_data.get("case_id") if inv_data else (st.session_state.active_case_id or "CASE-DEMO-001")
    account_id = inv_data.get("account_id") if inv_data else "ACC-B-001"
    report_data = st.session_state.report_data

    if not report_data and case_id:
        c_data = get_cached_case(case_id)
        if c_data and c_data.get("report"):
            report_data = c_data["report"]
            st.session_state.report_data = report_data

    if not report_data:
        st.info("No formal investigation report compiled yet. Click below to synthesize report from evidence.")
        if st.button("✨ Compile Investigation Report", type="primary", key="btn_compile_report"):
            with st.spinner("Compiling investigation report from structured evidence..."):
                rep_res = api_post(f"/cases/{case_id}/report", {})
                if rep_res and rep_res.get("report"):
                    report_data = rep_res["report"]
                    st.session_state.report_data = report_data
                    st.rerun()
        return

    exec_summary = report_data.get("executive_summary", f"Investigation completed for account {account_id}.")
    full_text = report_data.get("full_text", report_data.get("body", "Report narrative ready."))

    # Render header card without embedding markdown in HTML
    st.markdown(f"""
    <div class="chart-box-card" style="margin-bottom:14px;">
        <div class="chart-header-row">
            <div class="chart-title">Investigation Report &bull; {case_id} ({account_id})</div>
            <span class="high-risk-badge">{report_data.get('risk_band', 'HIGH')} RISK</span>
        </div>
        <div style="font-size:13.5px; line-height:1.6; color:#1e293b; margin-top:10px; padding:12px 14px; background:#f8fafc; border-left:3px solid #3b82f6; border-radius:6px;">
            <b>Executive Summary:</b> {exec_summary}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render report text directly via markdown parser
    st.markdown(full_text)

    # De-emphasized optional regulatory export & compliance review drawer
    with st.expander("⚖ Optional Regulatory Export & Review", expanded=False):
        st.caption(f"Optional regulatory export documents and formal compliance review sign-off for case `{case_id}`.")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇ Export Investigation Report (.md)",
                data=full_text,
                file_name=f"{case_id}_Investigation_Report.md",
                mime="text/markdown",
                width='stretch',
                key="btn_dl_sar_md",
            )
        with col2:
            dossier_html = get_cached_dossier(case_id)
            if dossier_html:
                st.download_button(
                    "⬇ Export Compliance Dossier (.html)",
                    data=str(dossier_html),
                    file_name=f"{case_id}_Compliance_Report.html",
                    mime="text/html",
                    width='stretch',
                    key="btn_dl_sar_html",
                )
        with st.form(key=f"report_disp_form_{case_id}"):
            action = st.selectbox("Compliance Determination", ["REQUEST_INFO", "ENHANCED_DILIGENCE", "FILE_SAR", "DISMISS_FALSE_POSITIVE"])
            notes = st.text_input("Investigator Notes", value="Corroborated rapid fund movement and new counterparty concentration.")
            disp_submit = st.form_submit_button("Record Determination")
            if disp_submit:
                api_post("/decisions", {"case_id": case_id, "action": action, "analyst_id": "OFFICER-7429", "reason_code": "TYP-01", "notes": notes})
                st.success(f"Determination recorded: {action}")


# ===========================================================================
# DEDICATED WORKSTATION PAGES
# ===========================================================================

# --- PAGE 1: DASHBOARD ---
def render_dashboard_page():
    """High-level system executive overview."""
    st.markdown('<h1 class="case-title">AML Investigation Dashboard</h1>', unsafe_allow_html=True)
    st.caption(APP_DESCRIPTION)

    alerts = get_cached_alerts()
    health = get_cached_health()

    total_alerts = len(alerts) if alerts else 0
    high_risk = sum(1 for a in alerts if a.get("risk_band") in ("HIGH", "CRITICAL")) if alerts else 0
    open_alerts = sum(1 for a in alerts if a.get("status", "").lower() in ("open", "in_review", "new")) if alerts else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-lavender">
            <div class="mini-stat-title">Total Prioritized Alerts</div>
            <div class="mini-stat-val">{total_alerts}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-pink">
            <div class="mini-stat-title">High / Critical Alerts</div>
            <div class="mini-stat-val">{high_risk}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-white">
            <div class="mini-stat-title">Active Investigations</div>
            <div class="mini-stat-val">{open_alerts}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-white">
            <div class="mini-stat-title">Average Alert Review Time</div>
            <div class="mini-stat-val">&lt; 2.0s</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    # Engine Status (Business Terminology)
    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown("""
        <div class="summary-card">
            <div class="summary-label">Investigation Service</div>
            <div class="summary-value"><span class="status-dot"></span> Operational (Port 8000)</div>
        </div>""", unsafe_allow_html=True)
    with h2:
        st.markdown("""
        <div class="summary-card">
            <div class="summary-label">Detection Models</div>
            <div class="summary-value"><span class="status-dot"></span> Active (3 Detection Models Active)</div>
        </div>""", unsafe_allow_html=True)
    with h3:
        st.markdown("""
        <div class="summary-card">
            <div class="summary-label">Evidence Store</div>
            <div class="summary-value"><span class="status-dot"></span> Persisted Investigation Records</div>
        </div>""", unsafe_allow_html=True)

    # Expandable Technical Infrastructure Details
    with st.expander("Technical Details", expanded=False):
        st.markdown("""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:4px;">
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px;">
                <div style="font-weight:700; font-size:12px; color:#0f172a; margin-bottom:4px;">Backend Infrastructure</div>
                <div style="font-size:11.5px; color:#475569;">
                    • <b>FastAPI</b> Investigation Service (Port 8000)<br>
                    • <b>SQLite / PostgreSQL</b> Evidence Store<br>
                    • <b>Forensic Audit Ledger:</b> Verifiable transaction hash-chain
                </div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px;">
                <div style="font-weight:700; font-size:12px; color:#0f172a; margin-bottom:4px;">Detection Models (Active: 3)</div>
                <div style="font-size:11.5px; color:#475569;">
                    • <b>XGBoost:</b> Supervised AML classifier (Weight: 20%)<br>
                    • <b>Isolation Forest:</b> Behavioral anomaly detector (Weight: 10%)<br>
                    • <b>Deep Autoencoder:</b> Unsupervised reconstruction (Weight: 10%)<br>
                    • <b>Network Risk Model:</b> Graph features (Weight: 15% - Fallback / Dev)
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Recent Alerts table
    st.markdown('<div class="chart-title" style="margin-bottom:10px;">Prioritized Alert Queue Snapshot</div>', unsafe_allow_html=True)
    if alerts:
        st.markdown("""
        <table class="custom-table" style="width:100%;">
            <thead><tr><th>Alert ID</th><th>Account</th><th>Priority</th><th>Risk Level</th><th>Primary Concern</th><th>Status</th></tr></thead>
            <tbody>
        """, unsafe_allow_html=True)
        for a in alerts[:6]:
            band = a.get("risk_band", "MEDIUM")
            pill = "state-pill-transfer" if band in ("HIGH", "CRITICAL") else "state-pill-treatment"
            st.markdown(f"""
            <tr>
                <td style="font-weight:700;">{a.get('alert_id')}</td>
                <td>{a.get('account_id')}</td>
                <td style="font-weight:800;">{a.get('priority_score', 0):.1f} / 100</td>
                <td><span class="{pill}">{band}</span></td>
                <td>{a.get('summary', '')[:90]}</td>
                <td><span class="status-dot"></span> Under Investigation</td>
            </tr>
            """, unsafe_allow_html=True)
        st.markdown("</tbody></table>", unsafe_allow_html=True)

        if st.button("Open Full Alert Queue ➔", type="primary"):
            st.session_state.current_page = "alert_queue"
            st.rerun()


# --- PAGE 2: ALERT QUEUE ---
def render_alert_queue_page():
    """Triage table with risk band filtering and 1-click launch."""
    st.markdown('<h1 class="case-title">Alert Queue</h1>', unsafe_allow_html=True)
    st.caption("Which alerts should I investigate first? Alerts prioritized dynamically by multi-signal risk assessment.")

    alerts = get_cached_alerts()
    if not alerts:
        st.info("No active alerts loaded in the system.")
        return

    f1, f2, f3 = st.columns([1.5, 1, 1])
    with f1:
        search_query = st.text_input("Search Alert / Account ID", placeholder="e.g. ACC-B-001 or SCENARIO-001", key="aq_search")
    with f2:
        selected_bands = st.multiselect("Risk Level Filter", ["CRITICAL", "HIGH", "MEDIUM", "LOW"], default=["CRITICAL", "HIGH", "MEDIUM", "LOW"], key="aq_bands")
    with f3:
        sort_order = st.selectbox("Sort By", ["Priority (Highest First)", "Priority (Lowest First)"], key="aq_sort")

    filtered = [a for a in alerts if a.get("risk_band", "MEDIUM") in selected_bands]
    if search_query:
        q = search_query.lower()
        filtered = [a for a in filtered if q in a.get("alert_id", "").lower() or q in a.get("account_id", "").lower() or q in a.get("summary", "").lower()]

    if "Lowest First" in sort_order:
        filtered.sort(key=lambda x: x.get("priority_score", 0))
    else:
        filtered.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

    st.markdown(f'<div style="font-size:12px; color:#64748b; margin-bottom:10px;">Showing {len(filtered)} alerts matching criteria</div>', unsafe_allow_html=True)

    for a in filtered:
        aid = a.get("alert_id", "")
        acc_id = a.get("account_id", "")
        score = a.get("priority_score", 0.0)
        band = a.get("risk_band", "MEDIUM")
        summary = a.get("summary", "Automated alert detected")

        pill = "state-pill-transfer" if band in ("HIGH", "CRITICAL") else "state-pill-treatment"

        c_row1, c_row2 = st.columns([4, 1])
        with c_row1:
            st.markdown(f"""
            <div style="background:#ffffff; border:1px solid #edf2f7; border-radius:8px; padding:10px 14px; margin-bottom:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-weight:700; color:#0f172a; font-size:13px;">{aid}</span>
                        <span style="color:#64748b; margin-left:8px; font-size:12px;">Account: <code>{acc_id}</code></span>
                    </div>
                    <div>
                        <span class="{pill}">{band}</span>
                        <span style="font-weight:800; font-size:14px; margin-left:8px; color:#0f172a;">{score:.1f} / 100</span>
                    </div>
                </div>
                <div style="font-size:12px; color:#475569; margin-top:4px;"><b>Primary Concern:</b> {summary}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_row2:
            if st.button(f"Investigate ➔", key=f"btn_triage_{aid}", width='stretch', type="primary" if aid == st.session_state.selected_alert_id else "secondary"):
                st.session_state.selected_alert_id = aid
                st.session_state.investigation_data = None
                st.session_state.report_data = None
                st.session_state.current_page = "workspace"
                st.rerun()


# --- PAGE 3: INVESTIGATION WORKSPACE ---
def render_workspace_page():
    """Primary investigation workspace with assistant stepper, signals, and tabbed deep dives."""
    alert_id = st.session_state.selected_alert_id
    alert_data = get_cached_alert(alert_id) if alert_id else None

    # Pipeline trigger
    if st.session_state.investigation_running:
        with st.spinner("Investigation Assistant executing structured analysis..."):
            run_investigation(alert_id)
            st.session_state.investigation_running = False
            st.rerun()

    inv_data = st.session_state.investigation_data

    case_headline = f"{alert_id}: {alert_data.get('summary', 'High-Velocity Multi-Hop Layering Alert')}" if alert_data else f"{alert_id}: High-Velocity Funnel Smurfing"

    render_top_header(case_headline, [
        ("Dashboard", "dashboard"),
        ("Alert Queue", "alert_queue"),
        ("Workspace", "workspace"),
    ])

    # Summary metrics
    render_summary_metrics(inv_data, alert_data)

    # Investigation Assistant Stepper
    render_investigator_stepper(inv_data)

    # Risk Indicators & Assessment
    render_risk_signals_and_models(inv_data, alert_data)

    st.markdown("<hr style='margin:20px 0; border:0; height:1px; background:#eef2f6;'>", unsafe_allow_html=True)

    # Embedded investigation tabs
    t_graph, t_timeline, t_evidence, t_why, t_whatif, t_report = st.tabs([
        "🕸 Transaction Network",
        "⏱ Activity Timeline",
        "📎 Investigation Evidence",
        "❓ Why Was This Alert Raised?",
        "⚡ Risk Drivers",
        "📄 Investigation Report",
    ])

    with t_graph:
        render_network_graph_view(alert_data, hops=st.session_state.graph_hops, key_prefix="tab")
    with t_timeline:
        render_timeline_and_flow_view(inv_data, alert_data)
    with t_evidence:
        render_evidence_ledger_view(inv_data, alert_data)
    with t_why:
        render_explainability_view(inv_data)
    with t_whatif:
        render_score_sensitivity_view(inv_data)
    with t_report:
        render_case_report_view(inv_data)


# --- PAGE 4: TRANSACTION NETWORK (STANDALONE) ---
def render_transaction_graph_page():
    alert_id = st.session_state.selected_alert_id
    alert_data = get_cached_alert(alert_id) if alert_id else None
    st.markdown('<h1 class="case-title">Transaction Network</h1>', unsafe_allow_html=True)
    st.caption("How did the money move between connected accounts? Explore transaction flows and counterparties.")

    render_network_graph_view(alert_data, hops=st.session_state.graph_hops, key_prefix="page")


# --- PAGE 5: ACTIVITY TIMELINE (STANDALONE) ---
def render_timeline_page():
    alert_id = st.session_state.selected_alert_id
    alert_data = get_cached_alert(alert_id) if alert_id else None
    inv_data = st.session_state.investigation_data
    st.markdown('<h1 class="case-title">Transaction Activity & Speed</h1>', unsafe_allow_html=True)
    st.caption("Review transaction activity and connected accounts over time.")
    render_timeline_and_flow_view(inv_data, alert_data)


# --- PAGE 6: INVESTIGATION EVIDENCE (STANDALONE) ---
def render_evidence_ledger_page():
    alert_id = st.session_state.selected_alert_id
    alert_data = get_cached_alert(alert_id) if alert_id else None
    inv_data = st.session_state.investigation_data
    st.markdown('<h1 class="case-title">Investigation Evidence</h1>', unsafe_allow_html=True)
    st.caption("What supports the finding? Supporting transactions, calculations, and observations for this case.")
    render_evidence_ledger_view(inv_data, alert_data)


# --- PAGE 7: WHY WAS THIS ALERT RAISED? (STANDALONE) ---
def render_explainability_page():
    inv_data = st.session_state.investigation_data
    st.markdown('<h1 class="case-title">Why Was This Alert Raised?</h1>', unsafe_allow_html=True)
    st.caption("Why was this alert prioritized? Key risk drivers, observable activity patterns, and supporting evidence.")
    render_explainability_view(inv_data)


# --- PAGE 8: RISK DRIVERS (STANDALONE) ---
def render_score_sensitivity_page():
    inv_data = st.session_state.investigation_data
    st.markdown('<h1 class="case-title">Risk Drivers</h1>', unsafe_allow_html=True)
    st.caption("What factors influenced the priority? Evaluate the impact of observable risk drivers.")
    render_score_sensitivity_view(inv_data)


# --- PAGE 9: CASE REPORT (STANDALONE) ---
def render_case_report_page():
    inv_data = st.session_state.investigation_data
    st.markdown('<h1 class="case-title">Investigation Report</h1>', unsafe_allow_html=True)
    st.caption("What should the investigator review? Structured case narrative with supporting evidence.")
    render_case_report_view(inv_data)


# --- PAGE 10: SETTINGS (MINIMAL) ---
def render_settings_page():
    """Minimal investigator workstation settings."""
    st.markdown('<h1 class="case-title">Settings</h1>', unsafe_allow_html=True)

    health = get_cached_health()
    api_status = health.get("status", "ok").upper()

    st.markdown('<div class="chart-title" style="margin-bottom:10px;">API Connection</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">API Service URL</div>
            <div class="summary-value"><code>{API_BASE}</code></div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Service Status</div>
            <div class="summary-value"><span class="status-dot"></span> {api_status} (v{health.get('version', '1.0.0')})</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="chart-title" style="margin-top:20px; margin-bottom:10px;">Demonstration Mode</div>', unsafe_allow_html=True)
    demo_mode = st.radio("Simulation Mode", [
        "Standard Benchmark Scenarios (1-9)",
        "Continuous Synthetic Live Radar Stream",
    ], index=0 if st.session_state.demo_mode == "Standard Benchmark Scenarios (1-9)" else 1)
    st.session_state.demo_mode = demo_mode

    st.markdown('<div class="chart-title" style="margin-top:20px; margin-bottom:10px;">Default Network Depth</div>', unsafe_allow_html=True)
    depth_label_map = {1: "1 level (Direct counterparties)", 2: "2 levels (Extended network)", 3: "3 levels (Wide network)"}
    hops_val = st.selectbox(
        "Default Depth",
        [1, 2, 3],
        index=st.session_state.graph_hops - 1,
        format_func=lambda x: depth_label_map.get(x, f"{x} levels"),
    )
    if hops_val != st.session_state.graph_hops:
        st.session_state.graph_hops = hops_val
        runtime_config.default_hops = hops_val

    st.markdown('<div class="chart-title" style="margin-top:20px; margin-bottom:10px;">Detection System Status</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:14px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:6px; font-size:12.5px;">
            <span><b>Detection Models:</b> 3 Active Models (XGBoost, Isolation Forest, Deep Autoencoder)</span>
            <span style="color:#10b981; font-weight:700;">● Operational</span>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12.5px;">
            <span><b>Graph Intelligence:</b> Relevance-Filtered Subgraph & Connected Account Traversal</span>
            <span style="color:#10b981; font-weight:700;">● Operational</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Technical Model & Architecture Details", expanded=False):
        st.markdown("""
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px;">
                <span><b>Supervised Risk Model (XGBoost):</b> 100 estimators, max depth 6 (Weight: 20%)</span>
                <span style="color:#10b981; font-weight:700;">● Active</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px;">
                <span><b>Behavioral Anomaly Model (Isolation Forest):</b> Contamination 0.05 (Weight: 10%)</span>
                <span style="color:#10b981; font-weight:700;">● Active</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px;">
                <span><b>Reconstruction Model (Deep Autoencoder):</b> 4-dim bottleneck latent space (Weight: 10%)</span>
                <span style="color:#10b981; font-weight:700;">● Active</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-size:12px;">
                <span><b>Network Risk Model (Graph Features):</b> Heuristic degree, centrality & fan-out (Weight: 15%)</span>
                <span style="color:#b45309; font-weight:700;">● Fallback / Development</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:12px;">
                <span><b>Forensic Heuristics (Fund Movement, Velocity, Counterparties):</b> 15% each (Total: 45%)</span>
                <span style="color:#10b981; font-weight:700;">● Active</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ===========================================================================
# MAIN ROUTING CONTROLLER
# ===========================================================================
def main():
    render_sidebar()

    page = st.session_state.current_page

    if page == "dashboard":
        render_dashboard_page()
    elif page == "alert_queue":
        render_alert_queue_page()
    elif page == "workspace":
        render_workspace_page()
    elif page == "graph":
        render_transaction_graph_page()
    elif page == "timeline":
        render_timeline_page()
    elif page == "evidence":
        render_evidence_ledger_page()
    elif page == "explainability":
        render_explainability_page()
    elif page == "sensitivity":
        render_score_sensitivity_page()
    elif page == "report":
        render_case_report_page()
    elif page == "settings":
        render_settings_page()
    else:
        render_workspace_page()


if __name__ == "__main__":
    main()
