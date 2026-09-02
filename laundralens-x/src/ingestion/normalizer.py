"""
LaundraLens X — Data Normalizer
Standardizes timestamps, currency strings, channel casings, and missing values.
"""
from __future__ import annotations

import pandas as pd


class DataNormalizer:
    @staticmethod
    def normalize_transactions(df: pd.DataFrame) -> pd.DataFrame:
        clean_df = df.copy()
        clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"])
        clean_df["amount"] = pd.to_numeric(clean_df["amount"], errors="coerce").fillna(0.0)
        clean_df["channel"] = clean_df["channel"].astype(str).str.upper().str.strip()
        clean_df["currency"] = clean_df["currency"].astype(str).str.upper().str.strip()
        if "transaction_type" in clean_df.columns:
            clean_df["transaction_type"] = clean_df["transaction_type"].astype(str).str.lower().str.strip()
        return clean_df

    @staticmethod
    def normalize_accounts(df: pd.DataFrame) -> pd.DataFrame:
        clean_df = df.copy()
        clean_df["account_id"] = clean_df["account_id"].astype(str).str.strip()
        clean_df["customer_id"] = clean_df["customer_id"].astype(str).str.strip()
        if "account_type" in clean_df.columns:
            clean_df["account_type"] = clean_df["account_type"].astype(str).str.lower().str.strip()
        return clean_df
