"""
LaundraLens X — Investigations API routes (fully implemented).
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.db.models import Investigation, Alert, Evidence, Finding, ModelScore, CaseMemory
from src.agents.orchestrator import InvestigationOrchestrator

logger = logging.getLogger("laundralens.api.investigations")
router = APIRouter(prefix="/investigations", tags=["investigations"])

# In-memory cache for active investigation results (for fast API reads)
_investigation_cache: dict = {}


class StartInvestigationRequest(BaseModel):
    alert_id: str
    force_rerun: bool = False


@router.post("")
def start_investigation(
    req: StartInvestigationRequest,
    db: Session = Depends(get_db),
):
    """Start a new investigation from an alert or load canonical snapshot."""
    from src.risk.snapshot import load_snapshot

    alert = db.query(Alert).filter(Alert.alert_id == req.alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {req.alert_id} not found")

    # Check for existing complete investigation unless force_rerun requested
    if not req.force_rerun:
        existing = db.query(Investigation).filter(
            Investigation.alert_id == req.alert_id,
            Investigation.status == "REPORT_READY",
        ).first()
        if existing:
            snap = load_snapshot(existing.case_id)
            if snap:
                _investigation_cache[existing.case_id] = snap.to_dict()
                return snap.to_dict()
            cached = _investigation_cache.get(existing.case_id, {})
            if cached:
                return cached

    # Deterministic case ID for demo scenario, or UUID for others
    if req.alert_id == "ALERT-SCENARIO-001":
        case_id = "CASE-DEMO-001"
    else:
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"

    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        inv = Investigation(
            case_id=case_id,
            alert_id=req.alert_id,
            account_id=alert.account_id,
            status="ALERT_CREATED",
        )
        db.add(inv)
        db.commit()

    # Run investigation (synchronous)
    try:
        orchestrator = InvestigationOrchestrator(
            case_id=case_id,
            alert_id=req.alert_id,
            account_id=alert.account_id,
        )
        result = orchestrator.run()
        _investigation_cache[case_id] = result
        return result
    except Exception as e:
        logger.error(f"Investigation failed for {case_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@router.get("/{case_id}")
def get_investigation(case_id: str, db: Session = Depends(get_db)):
    """Get investigation state and summary from canonical snapshot or DB."""
    from src.risk.snapshot import load_snapshot
    snap = load_snapshot(case_id)
    if snap:
        return snap.to_dict()

    cached = _investigation_cache.get(case_id)
    if cached:
        return cached

    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
    return {
        "case_id": inv.case_id,
        "alert_id": inv.alert_id,
        "account_id": inv.account_id,
        "status": inv.status,
        "summary": inv.summary,
        "priority_score": ms.final_score if ms else None,
        "risk_band": ms.risk_band if ms else None,
        "signals": {
            "behavior": ms.behavior_signal,
            "flow": ms.flow_signal,
            "temporal": ms.temporal_signal,
            "graph": ms.graph_signal,
        } if ms else {},
        "model_scores": {
            "xgboost_score": ms.xgboost_score,
            "isolation_score": ms.isolation_score,
            "autoencoder_score": ms.autoencoder_score,
        } if ms else {},
        "started_at": inv.started_at.isoformat() if inv.started_at else None,
        "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
    }


@router.get("/{case_id}/timeline")
def get_timeline(case_id: str, db: Session = Depends(get_db)):
    """Get investigation timeline events."""
    cached = _investigation_cache.get(case_id, {})
    timeline = cached.get("timeline", {})
    if timeline and timeline.get("events"):
        return timeline

    # Fallback: reconstruct from database
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        return {"case_id": case_id, "events": [], "count": 0}

    from src.agents import tools as T
    from src.agents.orchestrator import InvestigationOrchestrator
    orch = InvestigationOrchestrator(case_id, inv.alert_id or "", inv.account_id)
    txs_df = orch._load_transactions_df(db)
    alert_ts = inv.created_at or datetime(2026, 8, 14, 11, 30, 0)
    reconstructed = T.create_timeline(case_id, inv.account_id, txs_df, alert_ts)
    return reconstructed


@router.get("/{case_id}/evidence")
def get_evidence(case_id: str, db: Session = Depends(get_db)):
    """Get collected evidence items."""
    # Check cache
    cached = _investigation_cache.get(case_id, {})
    # Also load from DB
    ev_rows = db.query(Evidence).filter(Evidence.case_id == case_id).all()
    evidence_list = [{
        "evidence_id": e.evidence_id,
        "evidence_type": e.evidence_type,
        "account_id": e.account_id,
        "transaction_id": e.transaction_id,
        "source": e.source,
        "value": e.value,
        "calculation": e.calculation,
        "explanation": e.explanation,
    } for e in ev_rows]
    return {"case_id": case_id, "evidence": evidence_list, "count": len(evidence_list)}


@router.get("/{case_id}/explanations")
def get_explanations(case_id: str, db: Session = Depends(get_db)):
    """Get WHY explanations (SHAP + signal breakdown)."""
    cached = _investigation_cache.get(case_id, {})
    if cached.get("explanations") or cached.get("shap_contributions"):
        return {
            "case_id": case_id,
            "explanations": cached.get("explanations", []),
            "shap_contributions": cached.get("shap_contributions", {}),
        }

    # Fallback: reconstruct from ModelScore
    ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
    shap_vals = ms.shap_values if ms and ms.shap_values else {}
    explanations = []
    if ms:
        if ms.flow_signal and ms.flow_signal > 0.5:
            explanations.append({
                "signal": "Flow Signal",
                "value": round(ms.flow_signal, 3),
                "description": f"Elevated fund redistribution ({int(ms.flow_signal*100)}% signal strength) observed within observation horizon."
            })
        if ms.temporal_signal and ms.temporal_signal > 0.3:
            explanations.append({
                "signal": "Temporal Signal",
                "value": round(ms.temporal_signal, 3),
                "description": f"High velocity transaction bursts ({int(ms.temporal_signal*100)}% signal strength) detected."
            })
        if ms.behavior_signal and ms.behavior_signal > 0.3:
            explanations.append({
                "signal": "Behavioral Signal",
                "value": round(ms.behavior_signal, 3),
                "description": f"Substantial deviation from baseline ({int(ms.behavior_signal*100)}% signal strength)."
            })

    return {
        "case_id": case_id,
        "explanations": explanations,
        "shap_contributions": shap_vals,
    }


@router.get("/{case_id}/counterfactual")
def get_counterfactual(case_id: str, db: Session = Depends(get_db)):
    """Get score sensitivity / WHAT-IF analysis."""
    cached = _investigation_cache.get(case_id, {})
    if cached.get("counterfactual"):
        return {
            "case_id": case_id,
            "sensitivity": cached.get("counterfactual", {}),
            "label": "Score sensitivity",
            "disclaimer": "Shows signal contribution. Does not establish causation.",
        }

    # Fallback: check ModelScore table
    ms = db.query(ModelScore).filter(ModelScore.case_id == case_id).first()
    sensitivity = ms.counterfactual if ms and ms.counterfactual else {}
    if not sensitivity and ms:
        from src.risk.scorer import compute_counterfactual
        signals = {
            "flow": ms.flow_signal or 0.0,
            "temporal": ms.temporal_signal or 0.0,
            "behavior": ms.behavior_signal or 0.0,
            "graph": ms.graph_signal or 0.0,
            "xgboost": ms.xgboost_score or 0.5,
            "isolation_forest": ms.isolation_score or 0.5,
            "autoencoder": ms.autoencoder_score or 0.5,
        }
        sensitivity = compute_counterfactual(signals, ms.final_score or 50.0)

    return {
        "case_id": case_id,
        "sensitivity": sensitivity,
        "label": "Score sensitivity",
        "disclaimer": "Shows signal contribution. Does not establish causation.",
    }
