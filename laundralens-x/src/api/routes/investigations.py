"""Investigations API routes — stub, fully implemented in Phase 6."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.db.database import get_db
from src.db.models import Investigation, Alert

router = APIRouter(prefix="/investigations", tags=["investigations"])


class StartInvestigationRequest(BaseModel):
    alert_id: str


@router.post("")
def start_investigation(req: StartInvestigationRequest, db: Session = Depends(get_db)):
    """Start a new investigation from an alert. Full implementation in Phase 6."""
    alert = db.query(Alert).filter(Alert.alert_id == req.alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "message": "Investigation orchestrator not yet initialized",
        "alert_id": req.alert_id,
        "account_id": alert.account_id,
    }


@router.get("/{case_id}")
def get_investigation(case_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "case_id": inv.case_id,
        "alert_id": inv.alert_id,
        "account_id": inv.account_id,
        "status": inv.status,
        "summary": inv.summary,
        "started_at": inv.started_at.isoformat() if inv.started_at else None,
        "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
    }


@router.get("/{case_id}/timeline")
def get_timeline(case_id: str):
    return {"case_id": case_id, "events": [], "status": "timeline module not yet initialized"}


@router.get("/{case_id}/evidence")
def get_evidence(case_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.case_id == case_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {"case_id": case_id, "evidence": []}


@router.get("/{case_id}/explanations")
def get_explanations(case_id: str):
    return {"case_id": case_id, "explanations": [], "status": "explanation module not yet initialized"}


@router.get("/{case_id}/counterfactual")
def get_counterfactual(case_id: str):
    return {"case_id": case_id, "sensitivity": {}, "status": "counterfactual module not yet initialized"}
