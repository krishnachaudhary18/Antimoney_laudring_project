"""
LaundraLens X — Database Repositories
Clean data access abstraction for accounts, transactions, alerts, and investigations.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from src.db.models import Account, Customer, Transaction, Alert, Investigation, Evidence, Finding, ModelScore, CaseMemory


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, account_id: str) -> Optional[Account]:
        return self.db.query(Account).filter(Account.account_id == account_id).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Account]:
        return self.db.query(Account).offset(offset).limit(limit).all()

    def get_suspicious(self) -> List[Account]:
        return self.db.query(Account).filter(Account.is_synthetic_suspicious == True).all()


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, transaction_id: str) -> Optional[Transaction]:
        return self.db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()

    def get_for_account(
        self,
        account_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
    ) -> List[Transaction]:
        query = self.db.query(Transaction).filter(
            (Transaction.sender_account_id == account_id) | (Transaction.receiver_account_id == account_id)
        )
        if start_time:
            query = query.filter(Transaction.timestamp >= start_time)
        if end_time:
            query = query.filter(Transaction.timestamp <= end_time)
        return query.order_by(Transaction.timestamp.asc()).limit(limit).all()

    def to_dataframe(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> pd.DataFrame:
        query = self.db.query(Transaction)
        if start_time:
            query = query.filter(Transaction.timestamp >= start_time)
        if end_time:
            query = query.filter(Transaction.timestamp <= end_time)
        rows = query.all()
        if not rows:
            return pd.DataFrame()
        data = [{
            "transaction_id": r.transaction_id,
            "timestamp": r.timestamp,
            "sender_account_id": r.sender_account_id,
            "receiver_account_id": r.receiver_account_id,
            "amount": float(r.amount),
            "currency": r.currency,
            "channel": r.channel,
            "transaction_type": r.transaction_type,
            "scenario_id": r.scenario_id,
            "ground_truth_pattern": r.ground_truth_pattern,
        } for r in rows]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df


class AlertRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, alert_id: str) -> Optional[Alert]:
        return self.db.query(Alert).filter(Alert.alert_id == alert_id).first()

    def get_all(self, status: Optional[str] = None) -> List[Alert]:
        query = self.db.query(Alert)
        if status:
            query = query.filter(Alert.status == status)
        return query.order_by(desc(Alert.priority_score)).all()

    def update_status(self, alert_id: str, new_status: str) -> bool:
        alert = self.get_by_id(alert_id)
        if not alert:
            return False
        alert.status = new_status
        self.db.commit()
        return True


class InvestigationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_case_id(self, case_id: str) -> Optional[Investigation]:
        return self.db.query(Investigation).filter(Investigation.case_id == case_id).first()

    def get_by_alert_id(self, alert_id: str) -> Optional[Investigation]:
        return self.db.query(Investigation).filter(Investigation.alert_id == alert_id).first()

    def create(self, case_id: str, alert_id: str, account_id: str) -> Investigation:
        inv = Investigation(
            case_id=case_id,
            alert_id=alert_id,
            account_id=account_id,
            status="ALERT_CREATED",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)
        return inv
