"""Alerts API routes — placeholder, fully implemented in Phase 6."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.priority_score.desc()).all()
    return [
        {
            "alert_id": a.alert_id,
            "account_id": a.account_id,
            "priority_score": a.priority_score,
            "risk_band": a.risk_band,
            "status": a.status,
            "trigger_source": a.trigger_source,
            "summary": a.summary,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


@router.get("/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "alert_id": alert.alert_id,
        "account_id": alert.account_id,
        "priority_score": alert.priority_score,
        "risk_band": alert.risk_band,
        "status": alert.status,
        "trigger_source": alert.trigger_source,
        "summary": alert.summary,
        "scenario_id": alert.scenario_id,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }
