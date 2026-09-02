"""
LaundraLens X — Alerts API routes (fully implemented).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    """List all alerts sorted by priority score descending."""
    alerts = db.query(Alert).order_by(Alert.priority_score.desc()).all()
    return [{
        "alert_id": a.alert_id,
        "account_id": a.account_id,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "priority_score": a.priority_score,
        "risk_band": a.risk_band,
        "status": a.status,
        "summary": a.summary,
        "scenario_id": a.scenario_id,
    } for a in alerts]


@router.get("/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get specific alert details."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return {
        "alert_id": alert.alert_id,
        "account_id": alert.account_id,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "priority_score": alert.priority_score,
        "risk_band": alert.risk_band,
        "status": alert.status,
        "summary": alert.summary,
        "trigger_source": alert.trigger_source,
        "scenario_id": alert.scenario_id,
    }


@router.patch("/{alert_id}/status")
def update_alert_status(alert_id: str, status: str, db: Session = Depends(get_db)):
    """Update alert status (for human reviewer workflow)."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    valid_statuses = ["open", "in_review", "resolved", "escalated", "dismissed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    alert.status = status
    db.commit()
    return {"alert_id": alert_id, "status": status, "message": "Status updated"}
