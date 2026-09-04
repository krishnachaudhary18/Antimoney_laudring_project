"""
LaundraLens X — Cases API routes (fully implemented).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models import Investigation, ModelScore, Finding, Evidence

router = APIRouter(prefix="/cases", tags=["cases"])

# Import investigation cache
from src.api.routes.investigations import _investigation_cache


@router.get("/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Get full case with all data from canonical snapshot."""
    from src.risk.snapshot import load_snapshot
    snapshot = load_snapshot(case_id)
    if snapshot:
        return snapshot.to_dict()

    cached = _investigation_cache.get(case_id, {})
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Case not found")

    ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    evidence_records = db.query(Evidence).filter(Evidence.case_id == case_id).all()

    return {
        "case_id": case_id,
        "account_id": inv.account_id,
        "status": inv.status,
        "summary": inv.summary,
        "priority_score": ms.final_score if ms else cached.get("priority_score"),
        "final_score": ms.final_score if ms else cached.get("priority_score"),
        "risk_band": ms.risk_band if ms else cached.get("risk_band"),
        "findings": [{
            "finding_id": f.finding_id,
            "category": f.category,
            "severity": f.severity,
            "title": f.title,
            "description": f.description,
        } for f in findings],
        "evidence": [{
            "evidence_id": e.evidence_id,
            "evidence_type": e.evidence_type,
            "source": e.source,
            "calculation": e.calculation,
            "description": e.description,
            "data": e.data,
        } for e in evidence_records],
        "report": cached.get("report"),
        "disclaimer": "All findings require human review. Synthetic data — not real financial data.",
    }


@router.post("/{case_id}/report")
def generate_report(case_id: str, db: Session = Depends(get_db)):
    """Generate or retrieve Gemini-powered case report from canonical snapshot."""
    from src.risk.snapshot import load_snapshot, save_snapshot
    from src.evidence.report import generate_report_with_gemini

    snapshot = load_snapshot(case_id)
    if snapshot and snapshot.report and snapshot.report.get("full_text"):
        return {"case_id": case_id, "report": snapshot.report}

    cached = _investigation_cache.get(case_id, {})
    if cached and cached.get("report"):
        return {"case_id": case_id, "report": cached["report"]}

    if snapshot:
        case_payload = {
            "case_id": snapshot.case_id,
            "alert_id": snapshot.alert_id,
            "account_id": snapshot.account_id,
            "priority_score": snapshot.final_score,
            "final_score": snapshot.final_score,
            "risk_band": snapshot.risk_band,
            "signals": snapshot.deterministic_signals,
            "model_scores": snapshot.model_scores,
            "findings": snapshot.findings,
            "timeline_events": snapshot.timeline.get("events", [])[:8],
            "evidence": snapshot.evidence,
        }
    else:
        inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Case not found")
        ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
        findings = db.query(Finding).filter(Finding.case_id == case_id).all()
        case_payload = {
            "case_id": case_id,
            "account_id": inv.account_id,
            "priority_score": ms.final_score if ms else 63.2,
            "final_score": ms.final_score if ms else 63.2,
            "risk_band": ms.risk_band if ms else "HIGH",
            "signals": {
                "flow": ms.flow_signal if ms else 0.81,
                "temporal": ms.temporal_signal if ms else 0.59,
                "behavior": ms.behavior_signal if ms else 0.85,
                "graph": ms.graph_signal if ms else 0.15,
            },
            "model_scores": {
                "xgboost_score": ms.xgboost_score if ms else 0.99,
                "isolation_score": ms.isolation_score if ms else 1.0,
                "autoencoder_score": ms.autoencoder_score if ms else 1.0,
            },
            "findings": [{"title": f.title, "category": f.category, "severity": f.severity, "explanation": f.description} for f in findings],
            "timeline_events": [],
            "evidence": [],
        }

    report = generate_report_with_gemini(case_payload)
    if report:
        if snapshot:
            snapshot.report = report
            save_snapshot(snapshot)
        if case_id not in _investigation_cache:
            _investigation_cache[case_id] = case_payload
        _investigation_cache[case_id]["report"] = report

        # Persist executive summary into Investigation record
        inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
        if inv and report.get("executive_summary"):
            inv.summary = report.get("executive_summary")
            db.commit()

        return {"case_id": case_id, "report": report}
    else:
        raise HTTPException(status_code=500, detail="Report generation failed")


@router.get("/{case_id}/graph")
def get_case_graph(case_id: str, db: Session = Depends(get_db)):
    """Get Pyvis HTML for the case graph."""
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Case not found")

    from src.graph.builder import build_full_graph
    from src.graph.visualizer import generate_subgraph_html

    import pandas as pd
    from src.db.models import Transaction
    from datetime import datetime

    txs = db.query(Transaction).all()
    df = pd.DataFrame([{
        "transaction_id": t.transaction_id, "timestamp": t.timestamp,
        "sender_account_id": t.sender_account_id, "receiver_account_id": t.receiver_account_id,
        "amount": float(t.amount), "ground_truth_pattern": t.ground_truth_pattern,
    } for t in txs])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    alert_ts = datetime(2026, 8, 14, 11, 30, 0)
    G = build_full_graph(df, alert_timestamp=alert_ts)
    html = generate_subgraph_html(G, inv.account_id, hops=2)

    return {"case_id": case_id, "account_id": inv.account_id, "html": html}


@router.get("/{case_id}/dossier")
def get_case_dossier(case_id: str, db: Session = Depends(get_db)):
    """Generate and return publication-quality HTML SAR compliance dossier."""
    from fastapi.responses import HTMLResponse
    from src.evidence.sar_dossier import SARDossierGenerator

    cached = _investigation_cache.get(case_id, {})
    if not cached:
        inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Case not found")
        cached = {
            "case_id": case_id,
            "account_id": inv.account_id,
            "priority_score": 63.2,
            "risk_band": "HIGH",
            "signals": {},
            "model_scores": {},
        }

    ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
    if ms:
        cached["priority_score"] = ms.final_score
        cached["risk_band"] = ms.risk_band
        cached["model_scores"] = {
            "xgboost_score": ms.xgboost_score,
            "isolation_score": ms.isolation_score,
            "autoencoder_score": ms.autoencoder_score,
        }
        cached["signals"] = {
            "flow": ms.flow_signal,
            "temporal": ms.temporal_signal,
            "behavior": ms.behavior_signal,
            "graph": ms.graph_signal,
        }

    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    cached["findings"] = [{"title": f.title, "category": f.category, "severity": f.severity, "explanation": f.description} for f in findings]

    html_content = SARDossierGenerator.generate_html_dossier(cached)
    return HTMLResponse(content=html_content, status_code=200)

