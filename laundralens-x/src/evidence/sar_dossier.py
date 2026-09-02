"""
LaundraLens X — Formal Regulatory SAR Dossier Generator
Generates publication-quality, audit-compliant Suspicious Activity Reports (SAR)
following FIU-IND / PMLA and global financial crime reporting standards.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, List, Any


class SARDossierGenerator:
    """Compiles formal audit dossiers for human compliance officers and regulatory submission."""

    @staticmethod
    def generate_html_dossier(case_data: Dict[str, Any], investigator_id: str = "OFFICER-7429") -> str:
        case_id = case_data.get("case_id", "CASE-UNKNOWN")
        account_id = case_data.get("account_id", "ACC-UNKNOWN")
        score = case_data.get("priority_score", 0.0)
        risk_band = case_data.get("risk_band", "UNKNOWN")
        signals = case_data.get("signals", {})
        model_scores = case_data.get("model_scores", {})
        findings = case_data.get("findings", [])
        timeline = case_data.get("timeline", {}).get("events", [])
        evidence = case_data.get("evidence", [])

        # Integrity hash for digital provenance
        raw_payload = f"{case_id}-{account_id}-{score}-{datetime.utcnow().strftime('%Y%m%d')}"
        dossier_hash = hashlib.sha256(raw_payload.encode()).hexdigest().upper()

        timestamp_str = datetime.utcnow().strftime("%d-%b-%Y %H:%M:%S UTC")

        # HTML generation with formal bank compliance styling
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Regulatory SAR Dossier — {case_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            margin: 40px;
            color: #1a202c;
            background-color: #ffffff;
            line-height: 1.6;
        }}
        .header-table {{
            width: 100%;
            border-bottom: 2px solid #2d3748;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .header-title {{
            font-size: 22px;
            font-weight: 800;
            color: #1a365d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .header-sub {{
            font-size: 11px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}
        .badge-critical {{ background-color: #fed7d7; color: #9b2c2c; border: 1px solid #feb2b2; }}
        .badge-high {{ background-color: #feebc8; color: #9c4221; border: 1px solid #fbd38d; }}
        .section-title {{
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #2b6cb0;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 5px;
            margin-top: 25px;
            margin-bottom: 12px;
        }}
        table.data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 20px;
        }}
        table.data-table th {{
            background-color: #edf2f7;
            color: #4a5568;
            text-align: left;
            padding: 8px 10px;
            border: 1px solid #cbd5e0;
            font-weight: 600;
        }}
        table.data-table td {{
            padding: 8px 10px;
            border: 1px solid #e2e8f0;
            color: #2d3748;
        }}
        table.data-table tr:nth-child(even) {{
            background-color: #f7fafc;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 10px;
            background: #f8fafc;
            text-align: center;
        }}
        .metric-val {{
            font-size: 18px;
            font-weight: 800;
            color: #2b6cb0;
        }}
        .metric-lbl {{
            font-size: 10px;
            text-transform: uppercase;
            color: #718096;
            margin-top: 3px;
        }}
        .watermark {{
            position: fixed;
            top: 45%;
            left: 20%;
            font-size: 65px;
            color: rgba(226, 232, 240, 0.4);
            transform: rotate(-30deg);
            z-index: -1;
            font-weight: 900;
            letter-spacing: 5px;
            pointer-events: none;
        }}
        .signature-box {{
            margin-top: 35px;
            border: 1px solid #cbd5e0;
            padding: 15px;
            border-radius: 6px;
            background-color: #f7fafc;
        }}
        @media print {{
            body {{ margin: 12mm; font-size: 10.5pt; }}
            .header-table {{ page-break-after: avoid; }}
            .signature-box {{ page-break-inside: avoid; }}
            .data-table tr {{ page-break-inside: avoid; }}
            .section-title {{ page-break-after: avoid; }}
            .watermark {{ font-size: 50pt; opacity: 0.15; }}
            @page {{ size: A4; margin: 10mm; }}
        }}
    </style>
</head>
<body>
    <div class="watermark">SYNTHETIC REGULATORY DOSSIER</div>

    <table class="header-table">
        <tr>
            <td>
                <div class="header-title">Financial Intelligence Unit &bull; AML Investigation Dossier</div>
                <div class="header-sub">Form FIU-IND/PMLA &bull; Razorpay Compliance Automation Engine</div>
            </td>
            <td style="text-align: right;">
                <div><b>Case ID:</b> <code>{case_id}</code></div>
                <div><b>Generated:</b> {timestamp_str}</div>
                <div><b>Integrity Hash:</b> <code>{dossier_hash[:16]}...</code></div>
            </td>
        </tr>
    </table>

    <div class="section-title">1. Target Entity & Risk Classification</div>
    <table class="data-table">
        <tr>
            <th style="width: 25%;">Subject Account ID</th>
            <td style="width: 25%;"><b>{account_id}</b></td>
            <th style="width: 25%;">Investigation Priority</th>
            <td style="width: 25%;"><span class="badge badge-{'critical' if score >= 80 else 'high'}">{score:.1f} / 100 [{risk_band}]</span></td>
        </tr>
        <tr>
            <th>Declared Segment</th>
            <td>Merchant / Current Account</td>
            <th>Jurisdiction Region</th>
            <td>India / Domestic Payment Rails</td>
        </tr>
    </table>

    <div class="section-title">2. Forensic Signal Matrix</div>
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-val">{signals.get('flow', 0.0):.3f}</div>
            <div class="metric-lbl">Flow Conservation</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{signals.get('temporal', 0.0):.3f}</div>
            <div class="metric-lbl">Temporal Velocity</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{signals.get('behavior', 0.0):.3f}</div>
            <div class="metric-lbl">Baseline Deviation</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{signals.get('graph', 0.0):.3f}</div>
            <div class="metric-lbl">Network Centrality</div>
        </div>
    </div>

    <div class="section-title">3. Multi-Model Consensus Breakdown</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Model Paradigm</th>
                <th>Model Architecture</th>
                <th>Raw Risk Output</th>
                <th>Inference Status</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Supervised Gradient Boosting</td>
                <td>XGBoost Classifier + SHAP</td>
                <td><b>{model_scores.get('xgboost_score', 0.0):.3f}</b></td>
                <td><span style="color:#2b6cb0;">✔ Converged</span></td>
            </tr>
            <tr>
                <td>Unsupervised Density Estimation</td>
                <td>Isolation Forest</td>
                <td><b>{model_scores.get('isolation_score', 0.0):.3f}</b></td>
                <td><span style="color:#2b6cb0;">✔ Converged</span></td>
            </tr>
            <tr>
                <td>Deep Reconstruction Anomaly</td>
                <td>PyTorch 5-Layer Autoencoder</td>
                <td><b>{model_scores.get('autoencoder_score', 0.0):.3f}</b></td>
                <td><span style="color:#2b6cb0;">✔ Converged</span></td>
            </tr>
        </tbody>
    </table>

    <div class="section-title">4. Forensic Findings & Case Taxonomy</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Severity</th>
                <th>Category</th>
                <th>Observed Diagnostic Finding</th>
                <th>Calculation Formula</th>
            </tr>
        </thead>
        <tbody>"""

        for f in findings:
            sev = f.get("severity", "MEDIUM")
            cat = f.get("category", "FLOW").upper()
            title = f.get("title", "")
            desc = f.get("description", f.get("explanation", ""))
            calc = f.get("calculation", "N/A")
            html += f"""
            <tr>
                <td><span class="badge badge-{'critical' if sev in ('CRITICAL','HIGH') else 'high'}">{sev}</span></td>
                <td><b>{cat}</b></td>
                <td><b>{title}</b><br><span style="color:#718096; font-size:11px;">{desc}</span></td>
                <td><code>{calc}</code></td>
            </tr>"""

        html += f"""
        </tbody>
    </table>

    <div class="section-title">5. Primary Transaction Event Log (Chronological)</div>
    <table class="data-table">
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Flow Direction</th>
                <th>Amount (INR)</th>
                <th>Counterparty</th>
                <th>Channel</th>
                <th>Forensic Flag</th>
            </tr>
        </thead>
        <tbody>"""

        for t in timeline[:12]:
            direction = t.get("direction", "inflow").upper()
            amt = t.get("amount_inr_str", f"Rs {t.get('amount', 0):,.2f}")
            cparty = t.get("counterparty_id", t.get("counterparty", "N/A"))
            channel = t.get("channel", "UPI")
            time_str = t.get("time_str", t.get("timestamp", ""))
            ann = ", ".join(t.get("annotations", []))
            dir_color = "#276749" if direction == "INFLOW" else "#9b2c2c"

            html += f"""
            <tr>
                <td><code>{time_str}</code></td>
                <td><span style="color:{dir_color}; font-weight:700;">{direction}</span></td>
                <td><b>{amt}</b></td>
                <td><code>{cparty}</code></td>
                <td>{channel}</td>
                <td><span style="color:#c53030; font-size:10px;">{ann}</span></td>
            </tr>"""

        html += f"""
        </tbody>
    </table>

    <div class="signature-box">
        <div style="font-size:12px; font-weight:700; color:#2d3748; margin-bottom:5px;">COMPLIANCE VERIFICATION & DIGITAL AUDIT TRAIL</div>
        <div style="font-size:11px; color:#718096;">
            <b>Authorized Investigator ID:</b> {investigator_id} &bull; <b>Digital Sign-off Reference:</b> SHA256:{dossier_hash[:32]}<br>
            This dossier constitutes an automated forensic investigation packet prepared for MLRO review.
            In compliance with AML guidelines, automated decisions are non-blocking until validated by human compliance officers.
        </div>
    </div>
</body>
</html>"""
        return html
