"""
LaundraLens X — Analyst Disposition & Decisioning API Routes
Human-in-the-loop regulatory sign-off, SAR filing approval, and audit trails.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.db.database import get_db
from src.db.models import CaseDecision, Investigation

router = APIRouter(prefix="/decisions", tags=["decisions"])


class DecisionSubmissionRequest(BaseModel):
    case_id: str
    action: str  # FILE_SAR, REQUEST_INFO, ENHANCED_DILIGENCE, DISMISS_FALSE_POSITIVE
    analyst_id: str
    reason_code: str
    notes: Optional[str] = None


@router.post("")
def record_decision(req: DecisionSubmissionRequest, db: Session = Depends(get_db)):
    """Record an official compliance officer disposition on an investigated case."""
    inv = db.query(Investigation).filter(Investigation.case_id == req.case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Case {req.case_id} not found")

    valid_actions = ["FILE_SAR", "REQUEST_INFO", "ENHANCED_DILIGENCE", "DISMISS_FALSE_POSITIVE"]
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of {valid_actions}")

    decision = CaseDecision(
        decision_id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
        case_id=req.case_id,
        action=req.action,
        analyst_id=req.analyst_id,
        reason_code=req.reason_code,
        notes=req.notes,
        escalation_status="SUBMITTED_TO_FIU" if req.action == "FILE_SAR" else "DISPOSITIONED",
        disposition_timestamp=datetime.now(timezone.utc),
    )
    db.add(decision)

    # Update investigation status
    inv.status = f"DECIDED_{req.action}"
    db.commit()

    return {
        "decision_id": decision.decision_id,
        "case_id": req.case_id,
        "action": req.action,
        "escalation_status": decision.escalation_status,
        "analyst_id": req.analyst_id,
        "message": f"Case dispositioned with action: {req.action}",
    }


@router.get("/{case_id}")
def get_decisions(case_id: str, db: Session = Depends(get_db)):
    """Retrieve the complete disposition and decision audit log for a case."""
    records = db.query(CaseDecision).filter(CaseDecision.case_id == case_id).order_by(CaseDecision.disposition_timestamp.desc()).all()
    return [{
        "decision_id": d.decision_id,
        "case_id": d.case_id,
        "action": d.action,
        "analyst_id": d.analyst_id,
        "reason_code": d.reason_code,
        "notes": d.notes,
        "escalation_status": d.escalation_status,
        "timestamp": d.disposition_timestamp.isoformat() if d.disposition_timestamp else None,
    } for d in records]
