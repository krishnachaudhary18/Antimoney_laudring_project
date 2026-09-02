"""Accounts API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.db.database import get_db
from src.db.models import Account, Transaction

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/{account_id}")
def get_account(account_id: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "account_id": account.account_id,
        "customer_id": account.customer_id,
        "account_type": account.account_type,
        "segment": account.segment,
        "risk_profile": account.risk_profile,
        "status": account.status,
        "home_region": account.home_region,
        "creation_date": account.creation_date.isoformat() if account.creation_date else None,
        "is_synthetic_suspicious": account.is_synthetic_suspicious,
        "scenario_id": account.scenario_id,
    }


@router.get("/{account_id}/transactions")
def get_account_transactions(
    account_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    txs = (
        db.query(Transaction)
        .filter(
            (Transaction.sender_account_id == account_id) |
            (Transaction.receiver_account_id == account_id)
        )
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "transaction_id": t.transaction_id,
            "timestamp": t.timestamp.isoformat(),
            "sender_account_id": t.sender_account_id,
            "receiver_account_id": t.receiver_account_id,
            "amount": float(t.amount),
            "currency": t.currency,
            "channel": t.channel,
            "transaction_type": t.transaction_type,
            "status": t.status,
            "scenario_id": t.scenario_id,
        }
        for t in txs
    ]
