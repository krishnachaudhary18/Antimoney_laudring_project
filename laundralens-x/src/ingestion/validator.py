"""
LaundraLens X — Transaction & Account Data Validator
Validates schema, required fields, constraints, and data integrity.
"""
from __future__ import annotations

from typing import List, Dict, Tuple, Any
import pandas as pd
from pydantic import BaseModel, Field, field_validator


class TransactionSchema(BaseModel):
    transaction_id: str
    timestamp: str
    sender_account_id: str
    receiver_account_id: str
    amount: float = Field(gt=0.0)
    currency: str = "INR"
    channel: str
    transaction_type: str = "transfer"


class AccountSchema(BaseModel):
    account_id: str
    customer_id: str
    account_type: str
    segment: str
    risk_profile: str
    status: str = "active"


class DataValidator:
    """Validates raw CSV or DataFrame inputs before ingestion."""

    @staticmethod
    def validate_transactions(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        required_cols = ["transaction_id", "timestamp", "sender_account_id", "receiver_account_id", "amount"]
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")

        if errors:
            return False, errors

        # Check self-transfers
        self_transfers = df[df["sender_account_id"] == df["receiver_account_id"]]
        if not self_transfers.empty:
            errors.append(f"Found {len(self_transfers)} invalid self-transfers")

        # Check negative or zero amounts
        invalid_amounts = df[df["amount"] <= 0]
        if not invalid_amounts.empty:
            errors.append(f"Found {len(invalid_amounts)} non-positive transaction amounts")

        return len(errors) == 0, errors

    @staticmethod
    def validate_accounts(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        required_cols = ["account_id", "customer_id", "account_type", "segment"]
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Missing required account column: {col}")

        # Check uniqueness
        if df["account_id"].duplicated().any():
            errors.append("Duplicate account IDs detected")

        return len(errors) == 0, errors
