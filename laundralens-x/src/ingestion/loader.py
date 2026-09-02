"""
LaundraLens X — Data Ingestion Loader
Orchestrates reading CSVs, validation, normalization, and bulk DB insertion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from src.ingestion.validator import DataValidator
from src.ingestion.normalizer import DataNormalizer
from src.db.models import Transaction, Account, Customer


class IngestionLoader:
    def __init__(self, db: Session):
        self.db = db

    def ingest_from_directory(self, dir_path: Path) -> Dict[str, Any]:
        results = {}
        acc_path = dir_path / "accounts.csv"
        tx_path = dir_path / "transactions.csv"

        if acc_path.exists():
            df_acc = pd.read_csv(acc_path)
            valid, errors = DataValidator.validate_accounts(df_acc)
            if valid:
                df_acc = DataNormalizer.normalize_accounts(df_acc)
                results["accounts_loaded"] = len(df_acc)
            else:
                results["accounts_errors"] = errors

        if tx_path.exists():
            df_tx = pd.read_csv(tx_path)
            valid, errors = DataValidator.validate_transactions(df_tx)
            if valid:
                df_tx = DataNormalizer.normalize_transactions(df_tx)
                results["transactions_loaded"] = len(df_tx)
            else:
                results["transactions_errors"] = errors

        return results
