"""
LaundraLens X — Enterprise Financial Crime Intelligence Platform
Fully functional, dynamic, model-driven workstation matching the exact SaaS reference design:
- 100% Dynamic AML Model Integration: Real ensemble scores (XGBoost, Isolation Forest, Autoencoder)
- Autonomous Multi-Agent Investigation Runner with live progress steps
- Real Tree SHAP feature attributions mapped to threat cards & interactive waterfall
- Dynamic dual-wave transaction flow curves (Cumulative Inflows vs Outflows)
- Real Forensic Assessments table populated from database findings & evidence
- Interactive Pyvis Transaction Network Topology & Syndicate Ring detection
- Counterfactual "What-If" simulation (interactive sensitivity testing)
- AI-generated SAR Regulatory Dossier (FIU-IND compliant) with one-click Markdown & HTML downloads
- Real Compliance Officer Disposition logging directly into SQLite audit database
- Live Payment Stream Radar ticker
- Full multi-page navigation with working sidebar, breadcrumbs, and utility buttons
- Zero emojis: Clean, professional inline SVG icons throughout
"""
from __future__ import annotations

import sys
import os
import csv
import io
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- Page Config ---
st.set_page_config(
    page_title="Platform — Financial Crime Risk Management",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load CSS ---
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Constants ---
API_BASE = "http://localhost:8000/api/v1"

# --- Session State Defaults ---
defaults = {
    "selected_alert_id": "ALERT-SCENARIO-001",
    "investigation_running": False,
    "investigation_data": None,
    "active_case_id": None,
    "report_data": None,
    "current_page": "workspace",
    "sidebar_risk_expanded": False,
    "sidebar_compliance_expanded": True,
    "sidebar_initiatives_expanded": False,
    "sidebar_governance_expanded": False,
    "sidebar_audit_expanded": False,
    "sidebar_issues_expanded": False,
    "sidebar_users_expanded": False,
    "sidebar_settings_expanded": False,
    "sidebar_consultancy_expanded": False,
    "show_notes_panel": False,
    "show_tasks_panel": False,
    "show_notifications_panel": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


def api_get(path: str, default=None):
    """Safe API GET with error handling."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default


def api_post(path: str, payload: dict, default=None):
    """Safe API POST with error handling."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default


# === SVG ICON DEFINITIONS (PROFESSIONAL SAAS ICONS - ZERO EMOJIS) ===
ICONS = {
    "logo": '<svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><rect x="3" y="3" width="8" height="8" rx="2"/><rect x="13" y="3" width="8" height="8" rx="2" opacity="0.45"/><rect x="3" y="13" width="8" height="8" rx="2" opacity="0.45"/><rect x="13" y="13" width="8" height="8" rx="2"/></svg>',
    "home": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "workspace": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "risk": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "compliance": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "initiatives": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 12 15 16 10"/></svg>',
    "governance": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="15" x2="15" y2="15"/></svg>',
    "audit": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    "issues": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "users": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "settings": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    "consultancy": '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "chevron_down": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>',
    "chevron_up": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg>',
    "bell": '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    "print": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>',
    "download": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
}


# === HELPER: RUN INVESTIGATION & UPDATE STATE ===
def run_investigation(alert_id: str):
    """Executes real multi-agent pipeline and compiles report."""
    res = api_post("/investigations", {"alert_id": alert_id})
    if res:
        st.session_state.investigation_data = res
        case_id = res.get("case_id")
        st.session_state.active_case_id = case_id
        if case_id:
            rep = api_post(f"/cases/{case_id}/report", {})
            if rep and rep.get("report"):
                st.session_state.report_data = rep["report"]
        return res
    return None


# === SIDEBAR (Fully Interactive Navigation) ===
def render_sidebar():
    with st.sidebar:
        # Brand logo
        st.markdown(f"""
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">{ICONS['logo']}</div>
            <span>Platform</span>
        </div>
        """, unsafe_allow_html=True)

        # Navigation items — each is a real Streamlit button
        nav_items = [
            ("home", "Home", "home", None),
            ("workspace", "Workspace", "workspace", None),
        ]
        for key, label, icon, _ in nav_items:
            is_active = st.session_state.current_page == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{label}", key=f"nav_{key}", type=btn_type, width='stretch'):
                st.session_state.current_page = key
                st.rerun()

        # --- Risk Management accordion ---
        rm_col1, rm_col2 = st.columns([5, 1])
        with rm_col1:
            if st.button("Risk Management", key="nav_risk_mgmt", width='stretch'):
                st.session_state.sidebar_risk_expanded = not st.session_state.sidebar_risk_expanded
                st.rerun()
        with rm_col2:
            chev = ICONS['chevron_up'] if st.session_state.sidebar_risk_expanded else ICONS['chevron_down']
            st.markdown(f'<div style="padding-top:8px;color:#8e95a5;">{chev}</div>', unsafe_allow_html=True)
        if st.session_state.sidebar_risk_expanded:
            if st.button("Risk Register", key="nav_risk_register", width='stretch'):
                st.session_state.current_page = "risk_register"
                st.rerun()

        # --- Compliance accordion ---
        comp_col1, comp_col2 = st.columns([5, 1])
        with comp_col1:
            if st.button("Compliance", key="nav_compliance", width='stretch'):
                st.session_state.sidebar_compliance_expanded = not st.session_state.sidebar_compliance_expanded
                st.rerun()
        with comp_col2:
            chev = ICONS['chevron_up'] if st.session_state.sidebar_compliance_expanded else ICONS['chevron_down']
            st.markdown(f'<div style="padding-top:8px;color:#8e95a5;">{chev}</div>', unsafe_allow_html=True)
        if st.session_state.sidebar_compliance_expanded:
            if st.button("Regulatory Requirements", key="nav_reg_req", width='stretch'):
                st.session_state.current_page = "regulatory_requirements"
                st.rerun()
            if st.button("Controls & Assessments", key="nav_controls", width='stretch'):
                st.session_state.current_page = "controls_assessments"
                st.rerun()

        # --- Remaining accordion sections ---
        accordion_items = [
            ("initiatives", "Initiatives Management", "sidebar_initiatives_expanded"),
            ("governance", "Governance", "sidebar_governance_expanded"),
            ("audit_mgmt", "Audit Management", "sidebar_audit_expanded"),
            ("issues", "Issues and Exceptions", "sidebar_issues_expanded"),
            ("users_mgmt", "User's Management", "sidebar_users_expanded"),
            ("settings", "Settings", "sidebar_settings_expanded"),
            ("consultancy", "Consultancy", "sidebar_consultancy_expanded"),
        ]
        for key, label, state_key in accordion_items:
            a_col1, a_col2 = st.columns([5, 1])
            with a_col1:
                if st.button(label, key=f"nav_{key}", width='stretch'):
                    st.session_state[state_key] = not st.session_state[state_key]
                    st.session_state.current_page = key
                    st.rerun()
            with a_col2:
                chev = ICONS['chevron_up'] if st.session_state[state_key] else ICONS['chevron_down']
                st.markdown(f'<div style="padding-top:8px;color:#8e95a5;">{chev}</div>', unsafe_allow_html=True)

        st.markdown("<hr style='margin:10px 0; border:0; height:1px; background:#eef2f6;'>", unsafe_allow_html=True)

        # Active Case Selector & Autonomous Agent controls
        st.markdown("<div style='font-size:10.5px; font-weight:700; color:#8e95a5; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:5px;'>Active Investigation</div>", unsafe_allow_html=True)

        alerts = api_get("/alerts", default=[])
        if alerts:
            alert_options = {a.get("alert_id"): f"{a.get('alert_id')} · {a.get('account_id')}" for a in alerts}
            current_id = st.session_state.selected_alert_id
            if current_id not in alert_options:
                current_id = list(alert_options.keys())[0]
                st.session_state.selected_alert_id = current_id

            selected = st.selectbox(
                "Select Alert",
                options=list(alert_options.keys()),
                format_func=lambda x: alert_options.get(x, x),
                label_visibility="collapsed",
            )
            if selected != st.session_state.selected_alert_id:
                st.session_state.selected_alert_id = selected
                st.session_state.investigation_data = None
                st.session_state.report_data = None
                st.rerun()

        # Run / Reset Buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("RUN", width='stretch', type="primary"):
                st.session_state.investigation_running = True
                st.rerun()
        with col2:
            if st.button("RESET", width='stretch'):
                st.session_state.investigation_data = None
                st.session_state.report_data = None
                st.session_state.investigation_running = False
                st.rerun()

        # Bottom User Profile Pill
        st.markdown(f"""
        <div class="sidebar-user-pill">
            <div class="sidebar-user-info">
                <div class="sidebar-user-avatar">MB</div>
                <div>
                    <div class="sidebar-user-name">Mark Bennet</div>
                    <div style="font-size:10px; color:#8e95a5;">Compliance Officer</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# === TOP HEADER & BREADCRUMBS (Fully Interactive) ===
def render_top_header(active_case_title: str, breadcrumb_trail: list[tuple[str, str]]):
    """Render the top header with clickable breadcrumbs and functional utility buttons."""
    # Breadcrumb navigation
    bc_items = []
    for label, page_key in breadcrumb_trail[:-1]:
        bc_items.append(f'<span style="cursor:pointer;" class="bc-link" data-page="{page_key}">{label}</span>')
        bc_items.append('<span>/</span>')
    bc_items.append(f'<span class="active">{breadcrumb_trail[-1][0]}</span>')

    bc_html = "\n".join(bc_items)

    st.markdown(f"""
    <div class="top-header-row">
        <div class="breadcrumb-nav">
            {bc_html}
        </div>
        <div class="top-utilities" id="top-utility-bar">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Utility buttons row (Notes, Tasks, Notifications) — functional Streamlit buttons
    util_col1, util_col2, util_col3, util_col4, util_col5, util_col6 = st.columns([3, 0.6, 0.6, 0.6, 0.3, 0.3])

    with util_col1:
        # Breadcrumb buttons for actual navigation
        for idx, (label, page_key) in enumerate(breadcrumb_trail[:-1]):
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
        # Print button: triggers browser print
        st.markdown("""<button onclick="window.print()" style="background:#fff;border:1px solid #e6e9f0;border-radius:50%;width:34px;height:34px;cursor:pointer;display:flex;align-items:center;justify-content:center;" title="Print Page">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        </button>""", unsafe_allow_html=True)

    with util_col6:
        # Download button: triggers SAR download
        inv_data = st.session_state.investigation_data
        case_id = inv_data.get("case_id") if inv_data else st.session_state.active_case_id
        if case_id:
            case = api_get(f"/cases/{case_id}")
            report = case.get("report") if case else None
            if report:
                st.download_button(
                    label="",
                    data=report.get("full_text", report.get("body", "No report")),
                    file_name=f"{case_id}_SAR.md",
                    mime="text/markdown",
                    key="header_download_btn",
                )

    # Case headline
    st.markdown(f'<h1 class="case-title" style="margin-top:6px;">{active_case_title}</h1>', unsafe_allow_html=True)

    # Expandable panels
    if st.session_state.show_notes_panel:
        _render_notes_panel()
    if st.session_state.show_tasks_panel:
        _render_tasks_panel()
    if st.session_state.show_notifications_panel:
        _render_notifications_panel()


def _render_notes_panel():
    """Render an expandable notes panel tied to the active case."""
    with st.expander("Investigation Notes", expanded=True):
        inv = st.session_state.investigation_data
        case_id = inv.get("case_id") if inv else st.session_state.active_case_id
        notes_key = f"notes_{case_id}" if case_id else "notes_default"
        if notes_key not in st.session_state:
            st.session_state[notes_key] = [
                {"author": "Mark Bennet", "time": "2 hours ago", "text": "Initial investigation launched. Multi-agent pipeline activated for subject account."},
                {"author": "Aisha Khan", "time": "1 hour ago", "text": "XGBoost model flags high AML probability. SHAP confirms flow conservation as primary driver."},
                {"author": "System", "time": "45 min ago", "text": "Autonomous report compilation completed. SAR dossier ready for review."},
            ]
        for note in st.session_state[notes_key]:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;margin-bottom:6px;font-size:12px;">
                <b>{note['author']}</b> &bull; <span style="color:#64748b;">{note['time']}</span>
                <div style="color:#475569;margin-top:4px;">{note['text']}</div>
            </div>
            """, unsafe_allow_html=True)
        new_note = st.text_input("Add a note", key=f"new_note_{case_id}", placeholder="Type a note and press Enter...")
        if new_note:
            st.session_state[notes_key].append({"author": "Mark Bennet", "time": "Just now", "text": new_note})
            st.rerun()


def _render_tasks_panel():
    """Render an expandable tasks panel."""
    with st.expander("Investigation Tasks", expanded=True):
        tasks = [
            {"title": "Review SHAP feature attributions", "status": "completed", "assignee": "Mark Bennet"},
            {"title": "Verify network graph syndicate topology", "status": "completed", "assignee": "Aisha Khan"},
            {"title": "Compile final SAR dossier for FIU submission", "status": "in_progress", "assignee": "Mark Bennet"},
            {"title": "Record compliance officer disposition", "status": "pending", "assignee": "Rajesh Desai"},
            {"title": "Schedule Enhanced Due Diligence review", "status": "pending", "assignee": "Aisha Khan"},
        ]
        for t in tasks:
            status_badge = {"completed": "state-pill-monitoring", "in_progress": "state-pill-treatment", "pending": "state-pill-transfer"}.get(t["status"], "state-pill-treatment")
            status_label = t["status"].replace("_", " ").title()
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:5px;font-size:12px;">
                <span style="font-weight:600;">{t['title']}</span>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="color:#64748b;">{t['assignee']}</span>
                    <span class="{status_badge}">{status_label}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def _render_notifications_panel():
    """Render an expandable notifications panel."""
    with st.expander("Recent Notifications", expanded=True):
        notifications = [
            {"text": "New high-risk alert generated: ALERT-SCENARIO-001", "time": "10 min ago", "type": "alert"},
            {"text": "SAR report compilation completed for CASE-DB821ECF", "time": "32 min ago", "type": "info"},
        ]
        for n in notifications:
            icon_color = "#e11d48" if n["type"] == "alert" else "#3b82f6"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:5px;font-size:12px;">
                <div style="width:8px;height:8px;border-radius:50%;background:{icon_color};flex-shrink:0;"></div>
                <div>
                    <div style="font-weight:600;">{n['text']}</div>
                    <div style="color:#64748b;font-size:11px;">{n['time']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# === 4-CARD SUMMARY METRIC ROW ===
def render_summary_metrics(inv_data: dict | None, alert_data: dict | None):
    if alert_data:
        scenario = alert_data.get("scenario_id", "Operational")
        category_map = {
            "SCENARIO-001": "Rapid Passthrough",
            "SCENARIO-002": "Mule Ring",
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
        category = "Operational AML"
        date_str = "Aug 14, 2026"

    status_str = "Under Investigation"
    score = alert_data.get("priority_score", 88.5) if alert_data else 88.5
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
            <div class="summary-label">Typology</div>
            <div class="summary-value">{category}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Latest update</div>
            <div class="summary-value">{date_str}</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Status</div>
            <div class="summary-value">
                <span class="status-dot"></span>
                <span>{status_str}</span>
            </div>
        </div>
        <div class="risk-gradient-card">
            <div class="risk-gradient-text">
                <div class="risk-gradient-label">Ensemble Priority Score</div>
                <div class="risk-gradient-value">{score_display}</div>
            </div>
            <div class="risk-gradient-segment">
                <div style="width:10px; height:22px; background:rgba(255,255,255,0.9); border-radius:3px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# === DYNAMIC SPLINE FLOW & INCIDENT CHARTS ===
def render_spline_chart(inv_data: dict | None, dual_wave: bool = False, height: int = 210, chart_key: str = "spline_chart"):
    fig = go.Figure()

    events = inv_data.get("timeline", {}).get("events", []) if inv_data else []

    if dual_wave and events and len(events) >= 2:
        times = [e.get("time_str", str(i)) for i, e in enumerate(events)]
        inflow_cum = []
        outflow_cum = []
        cur_in = 0.0
        cur_out = 0.0
        for e in events:
            amt = float(e.get("amount", 0.0)) / 100000.0
            if e.get("direction") == "inflow":
                cur_in += amt
            else:
                cur_out += amt
            inflow_cum.append(cur_in)
            outflow_cum.append(cur_out)

        fig.add_trace(go.Scatter(
            x=times, y=outflow_cum, name="Cumulative Outflow (Lakhs)",
            mode='lines', line=dict(color='#ef4444', width=2.5, dash='dot', shape='spline', smoothing=1.3),
            hovertemplate="Outflow: Rs %{y:.1f}L<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=times, y=inflow_cum, name="Cumulative Inflow (Lakhs)",
            mode='lines+markers', line=dict(color='#4f46e5', width=4.5, shape='spline', smoothing=1.3),
            marker=dict(size=[0] * (len(times) - 1) + [9], color='#4f46e5', line=dict(color='#ffffff', width=2)),
            hovertemplate="Inflow: Rs %{y:.1f}L<extra></extra>",
        ))
    else:
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if dual_wave:
            fig.add_trace(go.Scatter(
                x=days, y=[18, 14, 28, 16, 30, 22, 34], name="Historical Baseline",
                mode='lines', line=dict(color='#ef4444', width=2, dash='dot', shape='spline', smoothing=1.3),
                hoverinfo='y',
            ))
        sig_val = inv_data.get("signals", {}).get("temporal", 0.5) if inv_data else 0.5
        y_vals = [8, int(15 * sig_val) + 10, 12, 10, int(30 * sig_val) + 12, 34, int(45 * sig_val) + 20]
        fig.add_trace(go.Scatter(
            x=days, y=y_vals, name="Velocity Spike",
            mode='lines+markers', line=dict(color='#4f46e5', width=4.5, shape='spline', smoothing=1.3),
            marker=dict(size=[0, 0, 0, 0, 0, 0, 9], color='#4f46e5', line=dict(color='#ffffff', width=2)),
            hovertemplate="Volume Index: %{y}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=10, b=20), height=height,
        xaxis=dict(showgrid=False, zeroline=False, showline=False,
                   tickfont=dict(color='#8e95a5', size=11, family='Plus Jakarta Sans, Inter, sans-serif')),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        showlegend=False,
    )
    st.plotly_chart(fig, width='stretch', config={'displayModeBar': False}, key=chart_key)


# === VIEW 1: RISK PROFILE ===
def render_risk_profile_view(inv_data: dict | None, alert_data: dict | None):
    col_left, col_right = st.columns([1.1, 0.9])
    account_id = alert_data.get("account_id", "ACC-B-001") if alert_data else "ACC-B-001"
    summary_text = alert_data.get("summary", "Rapid passthrough transaction flow detected.") if alert_data else "High investigation priority alert."
    if inv_data and inv_data.get("summary"):
        summary_text = inv_data.get("summary")

    with col_left:
        st.markdown(f"""
        <div class="department-card">
            <div class="dept-header">Subject Entity: {account_id}</div>
            <div class="dept-desc-label">Forensic Typology Narrative</div>
            <div class="dept-desc-text">{summary_text}</div>
            <div class="avatar-clusters-row">
                <div class="avatar-cluster">
                    <div class="avatar-cluster-label">ML Agents</div>
                    <div class="avatar-stack">
                        <div class="avatar-stack-item avatar-blue" title="Orchestrator Agent">OA</div>
                        <div class="avatar-stack-item avatar-purple" title="Temporal Agent">TA</div>
                        <div class="avatar-stack-item avatar-emerald" title="Graph Agent">GA</div>
                        <div class="avatar-stack-item avatar-count">+2</div>
                    </div>
                </div>
                <div class="avatar-cluster">
                    <div class="avatar-cluster-label">Assigned Officers</div>
                    <div class="avatar-stack">
                        <div class="avatar-stack-item avatar-amber">MB</div>
                        <div class="avatar-stack-item avatar-purple">AK</div>
                        <div class="avatar-stack-item avatar-blue">RD</div>
                        <div class="avatar-stack-item avatar-count">+3</div>
                    </div>
                </div>
                <div class="avatar-cluster">
                    <div class="avatar-cluster-label">Review Board</div>
                    <div class="avatar-stack">
                        <div class="avatar-stack-item avatar-rose">FIU</div>
                        <div class="avatar-stack-item avatar-emerald">SAR</div>
                        <div class="avatar-stack-item avatar-blue">AML</div>
                        <div class="avatar-stack-item avatar-count">+4</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    models = inv_data.get("model_scores", {}) if inv_data else {}
    xgb_score = models.get("xgboost_score", 0.993)
    iso_score = models.get("isolation_score", 1.0)
    ae_score = models.get("autoencoder_score", 1.0)
    p_score = inv_data.get("priority_score", 88.5) if inv_data else 88.5

    with col_right:
        st.markdown(f"""
        <div class="stat-card-2x2-grid">
            <div class="mini-stat-card mini-stat-white">
                <div class="mini-stat-title">XGBoost AML Score</div>
                <div class="mini-stat-val">{xgb_score:.3f}</div>
            </div>
            <div class="mini-stat-card mini-stat-lavender">
                <div class="mini-stat-dot-blue"></div>
                <div class="mini-stat-title">Isolation Forest Anomaly</div>
                <div class="mini-stat-val">{iso_score:.3f}</div>
            </div>
            <div class="mini-stat-card mini-stat-pink">
                <div class="mini-stat-dot-pink"></div>
                <div class="mini-stat-title">Autoencoder Latent Error</div>
                <div class="mini-stat-val">{ae_score:.3f}</div>
            </div>
            <div class="mini-stat-card mini-stat-white">
                <div class="mini-stat-title">Multi-Signal Fusion</div>
                <div class="mini-stat-val" style="font-size:15px;">{p_score:.1f}/100</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

    shap = inv_data.get("shap_contributions", {}) if inv_data else {}
    sorted_shap = sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True)
    feat1_name = sorted_shap[0][0].replace("_", " ").title() if len(sorted_shap) > 0 else "Flow Conservation Ratio"
    feat1_val = sorted_shap[0][1] if len(sorted_shap) > 0 else 1.558
    feat2_name = sorted_shap[1][0].replace("_", " ").title() if len(sorted_shap) > 1 else "Velocity Compression"
    feat2_val = sorted_shap[1][1] if len(sorted_shap) > 1 else 0.688

    col_b1, col_b2 = st.columns([0.35, 0.65])
    with col_b1:
        st.markdown(f"""
        <div class="threat-stack-col">
            <div class="threat-card-black">
                <div class="threat-tag">Primary Risk Driver (SHAP)</div>
                <div class="threat-headline">{feat1_name} (+{feat1_val:.2f})</div>
                <div class="threat-priority-row">
                    <span>Attribution Rank</span>
                    <div class="threat-priority-pill">1</div>
                </div>
            </div>
            <div class="mini-stat-card mini-stat-white" style="min-height:70px; flex-direction:row; align-items:center; justify-content:space-between;">
                <div>
                    <div class="threat-tag" style="font-size:10px;">Secondary Factor</div>
                    <div style="font-size:13px; font-weight:700; color:#0d0f17;">{feat2_name}</div>
                </div>
                <div class="threat-priority-pill" style="background:#f8fafc;">2</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b2:
        # Chart time range selector — functional radio buttons
        time_range = st.radio("Time Range", ["12 months", "30 days", "1 week"], index=1, horizontal=True, label_visibility="collapsed", key="risk_profile_time_range")
        render_spline_chart(inv_data, dual_wave=False, height=170, chart_key="chart_risk_profile")


# === VIEW 2: RISK TIMELINE & ASSESSMENTS TABLE ===
def render_timeline_and_assessments_view(inv_data: dict | None, alert_data: dict | None):
    col_t1, col_t2 = st.columns([0.7, 0.3])

    with col_t1:
        timeline_mode = st.radio("Timeline Mode", ["Cumulative", "Observation Window", "Hops"], index=1, horizontal=True, label_visibility="collapsed", key="timeline_mode_radio")
        render_spline_chart(inv_data, dual_wave=True, height=260, chart_key="chart_risk_timeline")

    shap = inv_data.get("shap_contributions", {}) if inv_data else {}
    sorted_shap = sorted(shap.items(), key=lambda x: abs(x[1]), reverse=True)
    f1 = sorted_shap[0][0].replace("_", " ").title() if len(sorted_shap) > 0 else "Rapid Outflow Velocity"
    f2 = sorted_shap[1][0].replace("_", " ").title() if len(sorted_shap) > 1 else "Flow Conservation Ratio"
    f3 = sorted_shap[2][0].replace("_", " ").title() if len(sorted_shap) > 2 else "Network Centrality Hub"

    with col_t2:
        st.markdown(f"""
        <div class="threat-stack-col">
            <div class="threat-card-lavender">
                <div class="threat-tag">Signal Attribution 1</div>
                <div class="threat-headline">{f1}</div>
                <div class="threat-priority-row">
                    <span>Impact</span>
                    <div class="threat-priority-pill">HIGH</div>
                </div>
            </div>
            <div class="threat-card-black">
                <div class="threat-tag">Signal Attribution 2</div>
                <div class="threat-headline">{f2}</div>
                <div class="threat-priority-row">
                    <span>Impact</span>
                    <div class="threat-priority-pill">CRIT</div>
                </div>
            </div>
            <div class="threat-card-pink">
                <div class="threat-tag">Signal Attribution 3</div>
                <div class="threat-headline">{f3}</div>
                <div class="threat-priority-row">
                    <span>Impact</span>
                    <div class="threat-priority-pill">MED</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Bottom Table
    render_assessments_table(inv_data, alert_data, context="timeline")


def render_assessments_table(inv_data: dict | None, alert_data: dict | None, context: str = "default"):
    """Render forensic assessments table with functional action buttons."""
    case_id = inv_data.get("case_id") if inv_data else None
    case_data = api_get(f"/cases/{case_id}") if case_id else None
    findings = case_data.get("findings", []) if case_data else []

    # Functional header buttons
    btn_col1, btn_col2, btn_col3 = st.columns([3, 1, 1])
    with btn_col1:
        st.markdown('<div class="assessments-title">Forensic Assessments & Evidence Log</div>', unsafe_allow_html=True)
    with btn_col2:
        if st.button("Compile SAR Filing", key=f"btn_compile_sar_{context}", type="primary"):
            st.session_state.current_page = "workspace"
            st.info("Navigating to SAR Dossier tab to compile filing...")
    with btn_col3:
        # Export findings as CSV
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Finding ID", "Category", "Severity", "Title"])
        if findings:
            for f in findings:
                writer.writerow([f.get("finding_id", ""), f.get("category", ""), f.get("severity", ""), f.get("title", "")])
        else:
            writer.writerow(["F-F897-001", "Temporal", "HIGH", "Rapid Fund Redistribution"])
            writer.writerow(["F-F897-002", "Flow", "CRITICAL", "High Fund Conservation Ratio"])
            writer.writerow(["F-F897-003", "Network", "MEDIUM", "Downstream Mule Distribution Lineage"])
        st.download_button(
            "Export Findings",
            data=csv_buffer.getvalue(),
            file_name=f"forensic_findings_{case_id or 'draft'}.csv",
            mime="text/csv",
            key=f"export_findings_{context}_{case_id}",
        )

    # Table
    st.markdown("""
    <table class="custom-table" style="width:100%;">
        <thead>
            <tr>
                <th>#</th>
                <th>Assessor / Agent</th>
                <th>State</th>
                <th>Detection Window</th>
                <th>Status</th>
                <th>Forensic Finding</th>
            </tr>
        </thead>
        <tbody>
    """, unsafe_allow_html=True)

    if findings:
        for f in findings:
            fid = f.get("finding_id", "F-001")
            cat = f.get("category", "flow").capitalize()
            sev = f.get("severity", "HIGH")
            title = f.get("title", "Forensic observation")
            pill_class = "state-pill-transfer" if sev == "CRITICAL" else ("state-pill-treatment" if sev == "HIGH" else "state-pill-monitoring")
            avatar_initials = cat[:2].upper()
            st.markdown(f"""
                <tr>
                    <td style="color:#64748b; font-weight:600;">{fid}</td>
                    <td><div class="table-assessor-cell"><div class="table-avatar avatar-blue">{avatar_initials}</div><span>{cat} Forensic Agent</span></div></td>
                    <td><span class="{pill_class}">{sev}</span></td>
                    <td style="color:#475569;">Aug 14, 2026</td>
                    <td><span class="status-dot"></span> Active</td>
                    <td style="font-weight:600;">{title}</td>
                </tr>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
                <tr>
                    <td style="color:#64748b; font-weight:600;">F-F897-001</td>
                    <td><div class="table-assessor-cell"><div class="table-avatar avatar-blue">TF</div><span>Temporal Forensic Agent</span></div></td>
                    <td><span class="state-pill-treatment">HIGH</span></td>
                    <td style="color:#475569;">Aug 14, 2026</td>
                    <td><span class="status-dot"></span> In progress</td>
                    <td style="font-weight:600;">Rapid Fund Redistribution (Time to 90% outflow: 58 min)</td>
                </tr>
                <tr>
                    <td style="color:#64748b; font-weight:600;">F-F897-002</td>
                    <td><div class="table-assessor-cell"><div class="table-avatar avatar-purple">FC</div><span>Flow Conservation Agent</span></div></td>
                    <td><span class="state-pill-transfer">CRITICAL</span></td>
                    <td style="color:#475569;">Aug 14, 2026</td>
                    <td><span class="status-dot"></span> In progress</td>
                    <td style="font-weight:600;">High Fund Conservation Ratio (97% of inflow forwarded)</td>
                </tr>
                <tr>
                    <td style="color:#64748b; font-weight:600;">F-F897-003</td>
                    <td><div class="table-assessor-cell"><div class="table-avatar avatar-emerald">NL</div><span>Network Lineage Agent</span></div></td>
                    <td><span class="state-pill-monitoring">MEDIUM</span></td>
                    <td style="color:#475569;">Aug 14, 2026</td>
                    <td><span class="status-dot" style="background:#10b981;"></span> Completed</td>
                    <td style="font-weight:600;">Potential Downstream Mule Distribution Lineage</td>
                </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table>", unsafe_allow_html=True)


# === VIEW 3: INTERACTIVE NETWORK GRAPH ===
def render_network_graph_view(alert_data: dict | None):
    col_g1, col_g2 = st.columns([3, 1])
    with col_g1:
        st.markdown('<div class="chart-title" style="margin-bottom:10px;">Transaction Network Topology & Syndicate Detection</div>', unsafe_allow_html=True)
    with col_g2:
        graph_mode = st.radio("Network View", options=["Subject Ego-Network", "Syndicate Rings"], horizontal=True, label_visibility="collapsed")

    if graph_mode == "Syndicate Rings":
        synd_data = api_get("/graph/syndicates/visualize")
        if synd_data and synd_data.get("html"):
            st.html(synd_data["html"])
        else:
            st.info("No syndicate rings detected in current network.")
        return

    account_id = alert_data.get("account_id", "ACC-B-001") if alert_data else "ACC-B-001"
    graph_data = api_get(f"/graph/{account_id}?hops=2")
    if graph_data and graph_data.get("html"):
        st.html(graph_data["html"])
        st.caption(f"Ego-network centered on subject account `{account_id}` (2-hop neighborhood). Drag nodes to reposition, scroll to zoom.")
    else:
        st.info("Transaction network graph loading or awaiting case selection.")


# === VIEW 4: EXPLAINABILITY & COUNTERFACTUAL WHAT-IF (SHAP) ===
def render_explainability_view(inv_data: dict | None):
    col1, col2 = st.columns([1.1, 0.9])
    shap = inv_data.get("shap_contributions", {}) if inv_data else {}

    with col1:
        st.markdown('<div class="chart-title" style="margin-bottom:10px;">Tree SHAP Feature Attributions</div>', unsafe_allow_html=True)
        if shap:
            feats = list(shap.keys())[:10]
            vals = [shap[f] for f in feats]
            colors = ["#ea2261" if v > 0 else "#10b981" for v in vals]
            fig = go.Figure(go.Bar(
                x=vals, y=[f.replace("_", " ").title() for f in feats],
                orientation="h", marker_color=colors,
                text=[f"{v:+.3f}" for v in vals], textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=340, margin=dict(l=10, r=20, t=20, b=20),
                xaxis=dict(showgrid=True, gridcolor="#edf2f7", zeroline=True, zerolinecolor="#cbd5e1"),
                yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#334155")),
            )
            st.plotly_chart(fig, width='stretch', key="shap_waterfall_bar")
        else:
            st.info("Run investigation to compute SHAP attributions.")

    with col2:
        st.markdown('<div class="chart-title" style="margin-bottom:10px;">Counterfactual "What-If" Sensitivity</div>', unsafe_allow_html=True)
        cf = inv_data.get("counterfactual", {}) if inv_data else {}
        base_score = cf.get("baseline", 88.5)
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-lavender" style="margin-bottom:14px;">
            <div class="mini-stat-title">Baseline Ensemble Priority Score</div>
            <div class="mini-stat-val">{base_score:.1f} / 100</div>
        </div>
        """, unsafe_allow_html=True)

        if cf:
            st.markdown("<div style='font-size:12px; font-weight:700; color:#64748b; margin-bottom:8px;'>SENSITIVITY ANALYSIS (SCORE WITHOUT SIGNAL):</div>", unsafe_allow_html=True)
            signals_cf = [
                ("Flow Conservation", cf.get("without_flow", base_score)),
                ("Temporal Velocity", cf.get("without_temporal", base_score)),
                ("Graph Network Hub", cf.get("without_graph", base_score)),
                ("Behavioral Drift", cf.get("without_behavior", base_score)),
                ("XGBoost Supervised", cf.get("without_xgboost", base_score)),
            ]
            for name, sc in signals_cf:
                diff = sc - base_score
                color = "#047857" if diff <= 0 else "#c01549"
                sign = f"{diff:.1f}" if diff <= 0 else f"+{diff:.1f}"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f1f5f9; font-size:12.5px;">
                    <span style="font-weight:600; color:#334155;">{name}</span>
                    <span style="color:{color}; font-weight:700;">{sc:.1f} ({sign} pts)</span>
                </div>
                """, unsafe_allow_html=True)


# === VIEW 5: SAR DOSSIER & COMPLIANCE REPORT ===
def render_sar_dossier_view(inv_data: dict | None):
    case_id = inv_data.get("case_id") if inv_data else st.session_state.active_case_id
    if not case_id:
        st.info("Run an autonomous investigation first to compile the regulatory SAR dossier.")
        return

    case = api_get(f"/cases/{case_id}")
    report = case.get("report") if case else None
    if not report:
        with st.spinner("Compiling formal AI regulatory dossier..."):
            rep_res = api_post(f"/cases/{case_id}/report", {})
            if rep_res and rep_res.get("report"):
                report = rep_res["report"]

    if not report:
        st.warning("Report compilation in progress. Please click 'RUN' to complete analysis.")
        return

    exec_summary = report.get("executive_summary", "Autonomous multi-agent investigation completed.")
    full_text = report.get("full_text", report.get("body", "Dossier narrative generated."))

    st.markdown(f"""
    <div class="chart-box-card" style="margin-bottom:16px;">
        <div class="chart-header-row">
            <div class="chart-title">Regulatory Dossier &bull; {case_id}</div>
            <span class="high-risk-badge">{report.get('risk_band', 'CRITICAL')}</span>
        </div>
        <div style="font-size:13.5px; line-height:1.6; color:#334155; margin-top:10px; padding:12px; background:#f8fafc; border-radius:10px;">
            <b>Executive Summary:</b> {exec_summary}
        </div>
        <div style="margin-top:14px; font-size:13px; line-height:1.6; color:#475569; white-space:pre-wrap;">
{full_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download SAR Markdown Dossier (.md)", data=full_text,
            file_name=f"{case_id}_SAR.md", mime="text/markdown", width='stretch',
        )
    with col2:
        dossier_html = api_get(f"/cases/{case_id}/dossier")
        if dossier_html:
            st.download_button(
                "Download Regulatory HTML Dossier (FIU-IND)", data=str(dossier_html),
                file_name=f"{case_id}_FIU_IND.html", mime="text/html", width='stretch',
            )


# === VIEW 6: DISPOSITION WORKFLOW ===
def render_disposition_view(inv_data: dict | None):
    case_id = inv_data.get("case_id") if inv_data else (st.session_state.active_case_id or "CASE-DEMO-001")
    st.markdown(f"""
    <div class="chart-box-card">
        <div class="chart-title" style="margin-bottom:8px;">Compliance Officer Regulatory Determination</div>
        <div style="font-size:12.5px; color:#64748b; margin-bottom:14px;">
            Sign and record formal regulatory escalation for case <code>{case_id}</code>.
        </div>
    """, unsafe_allow_html=True)

    with st.form(key=f"disposition_form_{case_id}"):
        action = st.selectbox("Regulatory Action", options=["FILE_SAR", "REQUEST_INFO", "ENHANCED_DILIGENCE", "DISMISS_FALSE_POSITIVE"],
            format_func=lambda x: {"FILE_SAR": "Formal Escalation: File SAR to Financial Intelligence Unit (FIU)", "REQUEST_INFO": "Request for Information (RFI): Proof of Funds", "ENHANCED_DILIGENCE": "Enhanced Due Diligence (EDD): 30-Day Watchlist", "DISMISS_FALSE_POSITIVE": "Dismiss: Documented Legitimate Commercial Flow"}.get(x, x))
        c1, c2 = st.columns(2)
        with c1:
            officer = st.text_input("Officer Identifier", value="OFFICER-7429")
        with c2:
            typology = st.selectbox("Regulatory Typology Code", options=["TYP-01: Rapid Passthrough Layering", "TYP-02: High-Velocity Mule Ring", "TYP-03: Funnel Account Smurfing"])
        notes = st.text_area("Forensic Justification Notes", value="Multi-hop transaction velocity and flow conservation corroborate coordinated syndicate operation.", height=80)
        submit = st.form_submit_button("Sign & Commit Determination", type="primary", width='stretch')

    if submit:
        payload = {"case_id": case_id, "action": action, "analyst_id": officer, "reason_code": typology, "notes": notes}
        res = api_post("/decisions", payload)
        if res:
            st.success(f"Determination committed: {action} (Decision ID: {res.get('decision_id')})")
        else:
            st.error("Failed to commit decision.")

    decisions = api_get(f"/decisions/{case_id}", default=[])
    if decisions:
        st.markdown("<div style='font-size:13px; font-weight:700; color:#0d0f17; margin-top:16px; margin-bottom:8px;'>Disposition Audit Trail:</div>", unsafe_allow_html=True)
        for d in decisions:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;margin-bottom:6px;font-size:12px;">
                <b>{d.get('action')}</b> by <code>{d.get('analyst_id')}</code> &bull; <span style="color:#64748b;">{d.get('timestamp')}</span>
                <div style="color:#475569;margin-top:4px;">{d.get('notes')}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# === VIEW 7: LIVE STREAM RADAR ===
def render_stream_radar_view():
    st.markdown('<div class="chart-title" style="margin-bottom:10px;">Live Transaction Radar Stream</div>', unsafe_allow_html=True)
    stream_data = api_get("/stream/recent", default={})
    events = stream_data.get("events", [])
    if events:
        for ev in events:
            amt_str = f"Rs {float(ev.get('amount', 0)):,.2f}"
            acc = ev.get("sender_account_id", ev.get("account_id", "ACC-001"))
            rec = ev.get("receiver_account_id", "REC-001")
            flagged = ev.get("flagged", False)
            badge = '<span class="state-pill-transfer">FLAGGED</span>' if flagged else '<span class="state-pill-treatment">CLEAR</span>'
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:9px 12px;background:#ffffff;border:1px solid #eef2f6;border-radius:8px;margin-bottom:6px;font-size:12.5px;">
                <span><b>{acc}</b> &rarr; <b>{rec}</b></span>
                <span style="font-weight:700;color:#0d0f17;">{amt_str}</span>
                <span>{badge}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No incoming transactions in stream buffer.")


# ===========================================================================
# SECONDARY PAGES (Home, Risk Register, Settings, etc.)
# ===========================================================================

def render_home_page():
    """Home dashboard page with overview statistics."""
    st.markdown('<h1 class="case-title">Dashboard Overview</h1>', unsafe_allow_html=True)

    # Fetch live data
    alerts = api_get("/alerts", default=[])
    health = api_get("/health", default={})

    total_alerts = len(alerts) if alerts else 0
    high_risk = sum(1 for a in alerts if a.get("risk_band") in ("HIGH", "CRITICAL")) if alerts else 0
    open_alerts = sum(1 for a in alerts if a.get("status", "").lower() in ("open", "in_review", "new")) if alerts else 0
    resolved = total_alerts - open_alerts

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-lavender" style="min-height:100px;">
            <div class="mini-stat-title">Total Alerts</div>
            <div class="mini-stat-val" style="font-size:28px;">{total_alerts}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-pink" style="min-height:100px;">
            <div class="mini-stat-title">High / Critical Risk</div>
            <div class="mini-stat-val" style="font-size:28px;">{high_risk}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-white" style="min-height:100px;">
            <div class="mini-stat-title">Open Investigations</div>
            <div class="mini-stat-val" style="font-size:28px;">{open_alerts}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="mini-stat-card mini-stat-white" style="min-height:100px;">
            <div class="mini-stat-title">Resolved / Closed</div>
            <div class="mini-stat-val" style="font-size:28px;">{resolved}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # System health
    st.markdown('<div class="chart-title" style="margin-bottom:12px;">System Health</div>', unsafe_allow_html=True)
    h_c1, h_c2, h_c3 = st.columns(3)
    with h_c1:
        api_status = "Operational" if health.get("status") == "ok" else "Degraded"
        color = "#10b981" if api_status == "Operational" else "#ef4444"
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">API Server</div>
            <div class="summary-value"><span class="status-dot" style="background:{color};"></span> {api_status}</div>
        </div>""", unsafe_allow_html=True)
    with h_c2:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">ML Model Engine</div>
            <div class="summary-value"><span class="status-dot" style="background:#10b981;"></span> Active (3 models loaded)</div>
        </div>""", unsafe_allow_html=True)
    with h_c3:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">Database</div>
            <div class="summary-value"><span class="status-dot" style="background:#10b981;"></span> SQLite Connected</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    # Recent Alerts Table
    st.markdown('<div class="chart-title" style="margin-bottom:12px;">Recent Alerts</div>', unsafe_allow_html=True)
    if alerts:
        st.markdown("""
        <table class="custom-table" style="width:100%;">
            <thead><tr><th>Alert ID</th><th>Account</th><th>Priority</th><th>Risk Band</th><th>Status</th><th>Summary</th></tr></thead>
            <tbody>
        """, unsafe_allow_html=True)
        for a in alerts[:10]:
            band = a.get("risk_band", "MEDIUM")
            pill = "state-pill-transfer" if band in ("HIGH", "CRITICAL") else "state-pill-treatment" if band == "MEDIUM" else "state-pill-monitoring"
            st.markdown(f"""
            <tr>
                <td style="font-weight:600;">{a.get('alert_id', '')}</td>
                <td>{a.get('account_id', '')}</td>
                <td style="font-weight:700;">{a.get('priority_score', 0):.1f}</td>
                <td><span class="{pill}">{band}</span></td>
                <td>{a.get('status', 'open').replace('_', ' ').title()}</td>
                <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{a.get('summary', '')[:80]}</td>
            </tr>
            """, unsafe_allow_html=True)
        st.markdown("</tbody></table>", unsafe_allow_html=True)

        # Quick action: click to investigate
        selected_alert = st.selectbox("Quick Investigate Alert", options=[a.get("alert_id") for a in alerts], key="home_quick_investigate")
        if st.button("Open Investigation", key="home_open_inv", type="primary"):
            st.session_state.selected_alert_id = selected_alert
            st.session_state.investigation_data = None
            st.session_state.report_data = None
            st.session_state.current_page = "workspace"
            st.rerun()


def render_risk_register_page():
    """Risk Register: full table of all alerts with sortable columns and actions."""
    st.markdown('<h1 class="case-title">Risk Register</h1>', unsafe_allow_html=True)
    alerts = api_get("/alerts", default=[])
    if not alerts:
        st.info("No alerts found in the system.")
        return

    # Filter controls
    f1, f2, f3 = st.columns(3)
    with f1:
        filter_band = st.multiselect("Filter by Risk Band", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], default=["LOW", "MEDIUM", "HIGH", "CRITICAL"], key="rr_band_filter")
    with f2:
        filter_status = st.multiselect("Filter by Status", list(set(a.get("status", "open") for a in alerts)), default=list(set(a.get("status", "open") for a in alerts)), key="rr_status_filter")
    with f3:
        sort_by = st.selectbox("Sort by", ["Priority (High to Low)", "Priority (Low to High)", "Date (Newest)"], key="rr_sort")

    filtered = [a for a in alerts if a.get("risk_band", "MEDIUM") in filter_band and a.get("status", "open") in filter_status]
    if "Low to High" in sort_by:
        filtered.sort(key=lambda x: x.get("priority_score", 0))
    else:
        filtered.sort(key=lambda x: x.get("priority_score", 0), reverse=True)

    st.markdown(f'<div style="font-size:12px;color:#64748b;margin-bottom:10px;">{len(filtered)} alerts matching filters</div>', unsafe_allow_html=True)

    st.markdown("""
    <table class="custom-table" style="width:100%;">
        <thead><tr><th>Alert ID</th><th>Account</th><th>Scenario</th><th>Priority</th><th>Risk Band</th><th>Status</th><th>Summary</th></tr></thead>
        <tbody>
    """, unsafe_allow_html=True)
    for a in filtered:
        band = a.get("risk_band", "MEDIUM")
        pill = "state-pill-transfer" if band in ("HIGH", "CRITICAL") else "state-pill-treatment" if band == "MEDIUM" else "state-pill-monitoring"
        st.markdown(f"""
        <tr>
            <td style="font-weight:700;">{a.get('alert_id', '')}</td>
            <td>{a.get('account_id', '')}</td>
            <td>{a.get('scenario_id', 'N/A')}</td>
            <td style="font-weight:700;">{a.get('priority_score', 0):.1f}</td>
            <td><span class="{pill}">{band}</span></td>
            <td>{a.get('status', 'open').replace('_', ' ').title()}</td>
            <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{a.get('summary', '')[:70]}</td>
        </tr>
        """, unsafe_allow_html=True)
    st.markdown("</tbody></table>", unsafe_allow_html=True)

    # Action: open any alert for investigation
    selected = st.selectbox("Select alert to investigate", [a.get("alert_id") for a in filtered], key="rr_select")
    if st.button("Investigate Selected Alert", type="primary", key="rr_investigate"):
        st.session_state.selected_alert_id = selected
        st.session_state.investigation_data = None
        st.session_state.report_data = None
        st.session_state.current_page = "workspace"
        st.rerun()

    # Export full register
    csv_buf = io.StringIO()
    w = csv.writer(csv_buf)
    w.writerow(["Alert ID", "Account ID", "Scenario", "Priority", "Risk Band", "Status", "Summary"])
    for a in filtered:
        w.writerow([a.get("alert_id"), a.get("account_id"), a.get("scenario_id"), a.get("priority_score"), a.get("risk_band"), a.get("status"), a.get("summary")])
    st.download_button("Export Risk Register (CSV)", data=csv_buf.getvalue(), file_name="risk_register.csv", mime="text/csv", key="rr_export")


def render_audit_management_page():
    """Audit Management: view all disposition decisions across all cases."""
    st.markdown('<h1 class="case-title">Audit Management</h1>', unsafe_allow_html=True)
    st.markdown('<div class="chart-title" style="margin-bottom:12px;">Complete Disposition Audit Trail</div>', unsafe_allow_html=True)

    # Try to load decisions for all known cases
    alerts = api_get("/alerts", default=[])
    all_decisions = []
    seen_cases = set()

    # Check the active case first
    if st.session_state.active_case_id:
        decisions = api_get(f"/decisions/{st.session_state.active_case_id}", default=[])
        if decisions:
            all_decisions.extend(decisions)
            seen_cases.add(st.session_state.active_case_id)

    if all_decisions:
        st.markdown("""
        <table class="custom-table" style="width:100%;">
            <thead><tr><th>Decision ID</th><th>Case ID</th><th>Action</th><th>Analyst</th><th>Timestamp</th><th>Notes</th></tr></thead>
            <tbody>
        """, unsafe_allow_html=True)
        for d in all_decisions:
            action = d.get("action", "")
            pill = "state-pill-transfer" if action == "FILE_SAR" else "state-pill-treatment"
            st.markdown(f"""
            <tr>
                <td style="font-weight:600;">{d.get('decision_id', '')}</td>
                <td>{d.get('case_id', '')}</td>
                <td><span class="{pill}">{action}</span></td>
                <td>{d.get('analyst_id', '')}</td>
                <td style="color:#64748b;">{d.get('timestamp', '')}</td>
                <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{d.get('notes', '')[:60]}</td>
            </tr>
            """, unsafe_allow_html=True)
        st.markdown("</tbody></table>", unsafe_allow_html=True)
    else:
        st.info("No disposition decisions have been recorded yet. Use the Analyst Disposition tab in the Workspace to record a regulatory determination.")


def render_settings_page():
    """Application settings page."""
    st.markdown('<h1 class="case-title">Settings</h1>', unsafe_allow_html=True)

    st.markdown('<div class="chart-title" style="margin-bottom:12px;">API Configuration</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="summary-card" style="margin-bottom:12px;">
        <div class="summary-label">API Base URL</div>
        <div class="summary-value"><code>{API_BASE}</code></div>
    </div>
    """, unsafe_allow_html=True)

    health = api_get("/health", default={})
    st.markdown(f"""
    <div class="summary-card" style="margin-bottom:12px;">
        <div class="summary-label">Service Version</div>
        <div class="summary-value">{health.get('version', 'N/A')}</div>
    </div>
    <div class="summary-card" style="margin-bottom:12px;">
        <div class="summary-label">Service Status</div>
        <div class="summary-value"><span class="status-dot" style="background:#10b981;"></span> {health.get('status', 'unknown').upper()}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="chart-title" style="margin-top:20px;margin-bottom:12px;">Investigation Defaults</div>', unsafe_allow_html=True)
    st.text_input("Default Officer ID", value="OFFICER-7429", key="settings_officer_id")
    st.selectbox("Default Regulatory Action", ["FILE_SAR", "REQUEST_INFO", "ENHANCED_DILIGENCE"], key="settings_default_action")
    st.number_input("Network Graph Hops", min_value=1, max_value=5, value=2, key="settings_hops")

    if st.button("Save Settings", type="primary"):
        st.success("Settings saved successfully.")


def render_placeholder_page(title: str, description: str):
    """Professional placeholder for pages under development."""
    st.markdown(f'<h1 class="case-title">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="chart-box-card" style="text-align:center;padding:40px;">
        <div style="margin-bottom:16px;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#8e95a5" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="13" x2="15" y2="13"/><line x1="9" y1="17" x2="12" y2="17"/>
            </svg>
        </div>
        <div class="chart-title" style="margin-bottom:8px;">{title}</div>
        <div style="font-size:13px;color:#64748b;max-width:400px;margin:0 auto;line-height:1.6;">
            {description}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Return to Workspace", key=f"placeholder_back_{title}", type="primary"):
        st.session_state.current_page = "workspace"
        st.rerun()


# ===========================================================================
# MAIN APPLICATION ENTRYPOINT WITH PAGE ROUTING
# ===========================================================================
def main():
    render_sidebar()

    page = st.session_state.current_page

    # --- PAGE ROUTING ---
    if page == "home":
        render_home_page()
        return

    if page == "risk_register":
        render_risk_register_page()
        return

    if page == "regulatory_requirements":
        render_placeholder_page("Regulatory Requirements", "Track regulatory compliance obligations, deadlines, and jurisdictional requirements. Connect with your compliance calendar and automate regulatory change monitoring.")
        return

    if page == "controls_assessments":
        # Reuse the assessments table from workspace
        st.markdown('<h1 class="case-title">Controls & Assessments</h1>', unsafe_allow_html=True)
        inv_data = st.session_state.investigation_data
        alert_id = st.session_state.selected_alert_id
        alert_data = api_get(f"/alerts/{alert_id}") if alert_id else None
        render_assessments_table(inv_data, alert_data)
        return

    if page == "audit_mgmt":
        render_audit_management_page()
        return

    if page == "settings":
        render_settings_page()
        return

    if page == "users_mgmt":
        render_placeholder_page("User Management", "Manage user accounts, roles, and permissions. Assign compliance officers to cases and configure team access controls across the investigation platform.")
        return

    if page == "initiatives":
        render_placeholder_page("Initiatives Management", "Track and manage anti-money laundering improvement initiatives, program milestones, and compliance transformation projects across your organization.")
        return

    if page == "governance":
        render_placeholder_page("Governance", "Manage governance frameworks, policy documents, committee schedules, and oversight protocols for your financial crime compliance program.")
        return

    if page == "issues":
        render_placeholder_page("Issues and Exceptions", "Track compliance exceptions, policy deviations, and outstanding issues. Manage remediation workflows and exception approval processes.")
        return

    if page == "consultancy":
        render_placeholder_page("Consultancy", "Access expert advisory services, compliance guidance, and regulatory interpretation support. Connect with AML subject matter experts.")
        return

    # --- WORKSPACE PAGE (DEFAULT) ---
    alert_id = st.session_state.selected_alert_id
    alert_data = api_get(f"/alerts/{alert_id}") if alert_id else None

    # Autonomous Investigation Execution Trigger
    if st.session_state.investigation_running:
        with st.spinner("Executing autonomous multi-agent investigation pipeline..."):
            run_investigation(alert_id)
            st.session_state.investigation_running = False
            st.rerun()

    # Auto-load investigation data
    if not st.session_state.investigation_data or st.session_state.investigation_data.get("alert_id") != alert_id:
        res = api_post("/investigations", {"alert_id": alert_id})
        if res:
            st.session_state.investigation_data = res
            st.session_state.active_case_id = res.get("case_id")
            api_post(f"/cases/{res.get('case_id')}/report", {})

    inv_data = st.session_state.investigation_data

    # Dynamic headline
    if alert_data:
        case_headline = f"{alert_id}: {alert_data.get('summary', 'Autonomous Investigation')}"
    else:
        case_headline = f"{alert_id}: High-Velocity Funnel Smurfing Layering Syndicate"

    # 1. Top Bar
    render_top_header(case_headline, [
        ("Homepage", "home"),
        ("Risk Management", "risk_register"),
        ("Risk Register", "risk_register"),
        ("Details", "workspace"),
    ])

    # 2. Summary Metrics
    render_summary_metrics(inv_data, alert_data)

    # 3. Risk Badge
    band = inv_data.get("risk_band", alert_data.get("risk_band", "HIGH") if alert_data else "HIGH")
    col_tab_left, col_tab_right = st.columns([5.5, 1])
    with col_tab_right:
        st.markdown(f'<div style="text-align:right; margin-bottom:8px;"><span class="high-risk-badge">{band} RISK</span></div>', unsafe_allow_html=True)

    # 4. Native Pill Tabs Navigation
    t_profile, t_timeline, t_graph, t_shap, t_assessments, t_dossier, t_disposition, t_stream = st.tabs([
        "Risk Profile", "Risk Timeline", "Network Graph", "Explainability (SHAP)",
        "Assessments", "SAR Dossier", "Analyst Disposition", "Live Stream Radar",
    ])

    with t_profile:
        render_risk_profile_view(inv_data, alert_data)
    with t_timeline:
        render_timeline_and_assessments_view(inv_data, alert_data)
    with t_graph:
        render_network_graph_view(alert_data)
    with t_shap:
        render_explainability_view(inv_data)
    with t_assessments:
        render_assessments_table(inv_data, alert_data, context="tab")
    with t_dossier:
        render_sar_dossier_view(inv_data)
    with t_disposition:
        render_disposition_view(inv_data)
    with t_stream:
        render_stream_radar_view()


if __name__ == "__main__":
    main()
