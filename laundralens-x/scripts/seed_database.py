"""
LaundraLens X — Database Seeder
Seeds the SQLite database from synthetic CSV files.
Also creates alerts for each suspicious scenario.

Usage:
    python scripts/seed_database.py
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
from sqlalchemy.orm import Session

from src.db.database import create_all_tables, SessionLocal
from src.db.models import Account, Customer, Transaction, Alert, Investigation

SYNTHETIC_DIR = ROOT / "data" / "synthetic"


def load_csvs():
    """Load all synthetic CSVs."""
    print("📂 Loading synthetic CSVs...")
    accounts_df = pd.read_csv(SYNTHETIC_DIR / "accounts.csv")
    customers_df = pd.read_csv(SYNTHETIC_DIR / "customers.csv")
    txs_df = pd.read_csv(SYNTHETIC_DIR / "transactions.csv")
    gt_df = pd.read_csv(SYNTHETIC_DIR / "ground_truth_scenarios.csv")
    print(f"   Accounts: {len(accounts_df)} | Customers: {len(customers_df)} | TXN: {len(txs_df)}")
    return accounts_df, customers_df, txs_df, gt_df


def seed_customers(db: Session, customers_df: pd.DataFrame):
    """Seed customers table."""
    existing = {c.customer_id for c in db.query(Customer.customer_id).all()}
    records = []
    for _, row in customers_df.iterrows():
        if row["customer_id"] in existing:
            continue
        records.append(Customer(
            customer_id=row["customer_id"],
            customer_type=row.get("customer_type", "individual"),
            occupation_or_business_category=row.get("occupation_or_business_category"),
            expected_activity_category=row.get("expected_activity_category"),
            geographic_region=row.get("geographic_region"),
        ))
    db.bulk_save_objects(records)
    db.commit()
    print(f"   ✅ Seeded {len(records)} new customers")


def seed_accounts(db: Session, accounts_df: pd.DataFrame):
    """Seed accounts table."""
    existing = {a.account_id for a in db.query(Account.account_id).all()}
    records = []
    for _, row in accounts_df.iterrows():
        if row["account_id"] in existing:
            continue
        creation = None
        if pd.notna(row.get("creation_date")):
            try:
                creation = datetime.fromisoformat(str(row["creation_date"]))
            except Exception:
                creation = None
        records.append(Account(
            account_id=row["account_id"],
            customer_id=row["customer_id"],
            account_type=row.get("account_type"),
            creation_date=creation,
            segment=row.get("segment"),
            risk_profile=row.get("risk_profile", "low"),
            status=row.get("status", "active"),
            home_region=row.get("home_region"),
            is_synthetic_suspicious=bool(row.get("is_synthetic_suspicious", False)),
            scenario_id=row.get("scenario_id") if pd.notna(row.get("scenario_id", None)) else None,
        ))
    db.bulk_save_objects(records)
    db.commit()
    print(f"   ✅ Seeded {len(records)} new accounts")


def seed_transactions(db: Session, txs_df: pd.DataFrame):
    """Seed transactions table (batch)."""
    existing = {t.transaction_id for t in db.query(Transaction.transaction_id).all()}
    records = []
    for _, row in txs_df.iterrows():
        if row["transaction_id"] in existing:
            continue
        ts = datetime.fromisoformat(str(row["timestamp"]))
        records.append(Transaction(
            transaction_id=row["transaction_id"],
            timestamp=ts,
            sender_account_id=row["sender_account_id"],
            receiver_account_id=row["receiver_account_id"],
            amount=float(row["amount"]),
            currency=row.get("currency", "INR"),
            channel=row.get("channel"),
            transaction_type=row.get("transaction_type", "transfer"),
            merchant_category=row.get("merchant_category") if pd.notna(row.get("merchant_category", None)) else None,
            location=row.get("location"),
            status=row.get("status", "completed"),
            scenario_id=row.get("scenario_id") if pd.notna(row.get("scenario_id", None)) else None,
            ground_truth_pattern=row.get("ground_truth_pattern") if pd.notna(row.get("ground_truth_pattern", None)) else None,
        ))

    # Batch insert in chunks to avoid SQLite limits
    CHUNK = 500
    for i in range(0, len(records), CHUNK):
        db.bulk_save_objects(records[i:i+CHUNK])
        db.commit()
    print(f"   ✅ Seeded {len(records)} new transactions")


def create_alerts(db: Session, gt_df: pd.DataFrame):
    """Create alerts for suspicious scenario accounts."""
    existing = {a.alert_id for a in db.query(Alert.alert_id).all()}

    # Priority scenario → score mappings
    SCENARIO_CONFIG = {
        "SCENARIO-001": {"priority": 91.0, "band": "CRITICAL", "summary": "Rapid redistribution of large inflow to multiple new counterparties within 58 minutes. Conservation ratio: 0.97. High investigation priority."},
        "SCENARIO-002": {"priority": 78.0, "band": "HIGH", "summary": "Account sent to 8 new recipients within 2 hours. Elevated new counterparty ratio."},
        "SCENARIO-003": {"priority": 72.0, "band": "HIGH", "summary": "Fan-in aggregation: 6 accounts transferred to single recipient."},
        "SCENARIO-004": {"priority": 68.0, "band": "HIGH", "summary": "Fan-out distribution: rapid transfers to 10 recipients."},
        "SCENARIO-005": {"priority": 65.0, "band": "HIGH", "summary": "Multi-hop transaction chain: A→B→C→D→E pattern detected."},
        "SCENARIO-006": {"priority": 55.0, "band": "MEDIUM", "summary": "Unusually large inflow for account profile. Amount significantly exceeds historical baseline."},
        "SCENARIO-007": {"priority": 58.0, "band": "MEDIUM", "summary": "Behavioral deviation: transaction amount 50x historical average for account type."},
        "SCENARIO-008": {"priority": 62.0, "band": "HIGH", "summary": "Temporal burst: 15 transactions in 30 minutes, high velocity signal."},
        "SCENARIO-009": {"priority": 75.0, "band": "HIGH", "summary": "Combined pattern: fan-in aggregation followed by rapid redistribution."},
    }

    primary_accounts = gt_df.drop_duplicates(subset=["scenario_id", "account_id"])
    new_alerts = []
    alert_id_map = {}  # scenario_id → alert_id for primary subject

    for _, row in primary_accounts.iterrows():
        scenario_id = row["scenario_id"]
        acc_id = row["account_id"]
        config = SCENARIO_CONFIG.get(scenario_id, {"priority": 40.0, "band": "MEDIUM", "summary": "Anomalous pattern detected."})

        alert_id = f"ALERT-{scenario_id}"
        if alert_id in existing:
            continue

        # Only create alert for primary subject of each scenario
        if scenario_id == "SCENARIO-001" and acc_id != "ACC-B-001":
            continue

        new_alerts.append(Alert(
            alert_id=alert_id,
            account_id=acc_id,
            created_at=datetime(2026, 8, 14, 11, 30, 0),
            priority_score=config["priority"],
            risk_band=config["band"],
            trigger_source="ml_model",
            status="open",
            summary=config["summary"],
            scenario_id=scenario_id,
        ))
        alert_id_map[scenario_id] = alert_id

    db.bulk_save_objects(new_alerts)
    db.commit()
    print(f"   ✅ Created {len(new_alerts)} alerts")
    return alert_id_map


def create_demo_investigation(db: Session, alert_id_map: dict):
    """Create the primary demo investigation record."""
    DEMO_CASE_ID = "CASE-DEMO-001"
    existing = db.query(Investigation).filter(Investigation.case_id == DEMO_CASE_ID).first()
    if existing:
        print("   ℹ  Demo investigation already exists")
        return

    alert_id = alert_id_map.get("SCENARIO-001", "ALERT-SCENARIO-001")
    inv = Investigation(
        case_id=DEMO_CASE_ID,
        alert_id=alert_id,
        account_id="ACC-B-001",
        status="ALERT_CREATED",
        agent_version="1.0.0",
        created_at=datetime(2026, 8, 14, 11, 30, 0),
    )
    db.add(inv)
    db.commit()
    print(f"   ✅ Demo investigation {DEMO_CASE_ID} created")


def main():
    print("🌱 LaundraLens X — Database Seeder")
    print()

    # Ensure tables exist
    print("🗄  Initializing database tables...")
    create_all_tables()
    print("   ✅ Tables ready")

    # Load CSVs
    accounts_df, customers_df, txs_df, gt_df = load_csvs()

    with SessionLocal() as db:
        print("\n👥 Seeding customers...")
        seed_customers(db, customers_df)

        print("🏦 Seeding accounts...")
        seed_accounts(db, accounts_df)

        print("💸 Seeding transactions...")
        seed_transactions(db, txs_df)

        print("🚨 Creating alerts...")
        alert_id_map = create_alerts(db, gt_df)

        print("🔍 Creating demo investigation...")
        create_demo_investigation(db, alert_id_map)

    print("\n✅ Database seeded successfully!")
    print("   Primary demo case: CASE-DEMO-001 → Account ACC-B-001")
    print("   Alert: ALERT-SCENARIO-001 → Risk Band: CRITICAL")
    print()
    print("Next steps:")
    print("  python scripts/train_models.py    # train ML models")
    print("  uvicorn src.api.main:app --reload # start API")
    print("  streamlit run dashboard/app.py    # start dashboard")


if __name__ == "__main__":
    main()
