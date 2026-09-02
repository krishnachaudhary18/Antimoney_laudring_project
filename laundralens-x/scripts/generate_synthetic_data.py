"""
LaundraLens X — Synthetic Data Generator
Generates realistic financial transactions with 9 planted suspicious scenarios.

Usage:
    python scripts/generate_synthetic_data.py

Output:
    data/synthetic/accounts.csv
    data/synthetic/customers.csv
    data/synthetic/transactions.csv
    data/synthetic/ground_truth_scenarios.csv
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import numpy as np
import pandas as pd
from faker import Faker

# Deterministic seed
DEMO_SEED = 42
random.seed(DEMO_SEED)
np.random.seed(DEMO_SEED)
fake = Faker("en_IN")
fake.seed_instance(DEMO_SEED)

# ── Configuration ──────────────────────────────────────────────────
N_ACCOUNTS = 500
N_NORMAL_TRANSACTIONS = 5000
DATE_END = datetime(2026, 8, 14, 12, 0, 0)   # end of normal period
DATE_START = DATE_END - timedelta(days=30)
DEMO_DAY = datetime(2026, 8, 14, 10, 0, 0)   # day of suspicious activity

CHANNELS = ["UPI", "NEFT", "RTGS", "IMPS", "CASH"]
CHANNEL_WEIGHTS = [0.45, 0.20, 0.10, 0.20, 0.05]
REGIONS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune", "Kolkata", "Ahmedabad"]
MERCHANT_CATEGORIES = ["groceries", "utilities", "rent", "shopping", "fuel", "restaurant", "medical", "subscription"]

# Account behavioral profiles
PROFILES = {
    "salary": {"inflow_mean": 80000, "inflow_std": 5000, "outflow_mean": 60000, "outflow_std": 8000, "tx_per_day": 3},
    "student": {"inflow_mean": 15000, "inflow_std": 2000, "outflow_mean": 12000, "outflow_std": 3000, "tx_per_day": 1},
    "merchant": {"inflow_mean": 200000, "inflow_std": 50000, "outflow_mean": 180000, "outflow_std": 40000, "tx_per_day": 15},
    "small_business": {"inflow_mean": 500000, "inflow_std": 100000, "outflow_mean": 450000, "outflow_std": 80000, "tx_per_day": 8},
}

PROFILE_WEIGHTS = [0.50, 0.20, 0.20, 0.10]   # salary, student, merchant, small_business
PROFILE_NAMES = list(PROFILES.keys())

# ── Reserved demo accounts ─────────────────────────────────────────
DEMO_ACCOUNTS = {
    "ACC-A-001": ("CUST-A-001", "small_business"),   # source of large inflow
    "ACC-B-001": ("CUST-B-001", "merchant"),          # primary suspect (rapid redistribution)
    "ACC-C-001": ("CUST-C-001", "salary"),
    "ACC-D-001": ("CUST-D-001", "salary"),
    "ACC-E-001": ("CUST-E-001", "student"),
    "ACC-F-001": ("CUST-F-001", "salary"),
    "ACC-G-001": ("CUST-G-001", "student"),           # downstream from E
}

# ── Suspicious scenario account pools ─────────────────────────────
SCENARIO_ACCOUNTS: Dict[str, List[str]] = {}


def make_id(prefix: str = "ACC") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def random_amount(mean: float, std: float, min_val: float = 1.0) -> float:
    return max(min_val, round(abs(np.random.normal(mean, std)), 2))


def random_timestamp(start: datetime, end: datetime) -> datetime:
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def random_channel() -> str:
    return random.choices(CHANNELS, weights=CHANNEL_WEIGHTS, k=1)[0]


# ══════════════════════════════════════════════════════════════════
# CUSTOMER GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_customers(accounts_df: pd.DataFrame) -> pd.DataFrame:
    """Build customer records from account data."""
    records = []
    seen = set()
    for _, row in accounts_df.iterrows():
        cid = row["customer_id"]
        if cid in seen:
            continue
        seen.add(cid)
        profile = row["expected_activity_category"]
        records.append({
            "customer_id": cid,
            "customer_type": "business" if profile in ("merchant", "small_business") else "individual",
            "occupation_or_business_category": profile,
            "expected_activity_category": profile,
            "geographic_region": random.choice(REGIONS),
        })
    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════
# ACCOUNT GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_accounts() -> pd.DataFrame:
    records = []

    # 1. Add demo scenario accounts first
    for acc_id, (cust_id, profile) in DEMO_ACCOUNTS.items():
        records.append({
            "account_id": acc_id,
            "customer_id": cust_id,
            "account_type": "current" if profile in ("merchant", "small_business") else "savings",
            "creation_date": (DATE_START - timedelta(days=random.randint(30, 365))).isoformat(),
            "segment": "sme" if profile in ("small_business",) else "retail",
            "risk_profile": "low",
            "status": "active",
            "home_region": "Mumbai",
            "expected_activity_category": profile,
            "is_synthetic_suspicious": acc_id == "ACC-B-001",
            "scenario_id": "SCENARIO-001" if acc_id in ("ACC-B-001", "ACC-A-001") else None,
        })

    # 2. Generate regular accounts to fill up to N_ACCOUNTS
    n_regular = N_ACCOUNTS - len(DEMO_ACCOUNTS)
    for i in range(n_regular):
        profile = random.choices(PROFILE_NAMES, weights=PROFILE_WEIGHTS, k=1)[0]
        acc_id = f"ACC-{i+100:04d}"
        cust_id = f"CUST-{i+100:04d}"
        acc_type = "current" if profile in ("merchant", "small_business") else "savings"
        segment = "sme" if profile == "small_business" else ("corporate" if profile == "merchant" else "retail")
        creation = DATE_START - timedelta(days=random.randint(30, 2000))
        records.append({
            "account_id": acc_id,
            "customer_id": cust_id,
            "account_type": acc_type,
            "creation_date": creation.isoformat(),
            "segment": segment,
            "risk_profile": "low",
            "status": "active",
            "home_region": random.choice(REGIONS),
            "expected_activity_category": profile,
            "is_synthetic_suspicious": False,
            "scenario_id": None,
        })

    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════
# NORMAL TRANSACTION GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_normal_transactions(accounts: pd.DataFrame) -> List[Dict]:
    """Generate realistic normal transactions for non-suspicious accounts."""
    txs = []
    regular_accs = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    n = 0

    while n < N_NORMAL_TRANSACTIONS:
        sender_id = random.choice(regular_accs)
        receiver_id = random.choice([a for a in regular_accs if a != sender_id])

        profile_row = accounts[accounts["account_id"] == sender_id].iloc[0]
        profile = PROFILES.get(profile_row["expected_activity_category"], PROFILES["salary"])
        amount = random_amount(profile["outflow_mean"] / profile["tx_per_day"], profile["outflow_std"] / 2, 10)

        ts = random_timestamp(DATE_START, DATE_END - timedelta(hours=6))
        txs.append({
            "transaction_id": f"TXN-{uuid.uuid4().hex[:12].upper()}",
            "timestamp": ts.isoformat(),
            "sender_account_id": sender_id,
            "receiver_account_id": receiver_id,
            "amount": round(amount, 2),
            "currency": "INR",
            "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": random.choice(MERCHANT_CATEGORIES + [None, None]),
            "location": random.choice(REGIONS),
            "status": "completed",
            "scenario_id": None,
            "ground_truth_pattern": None,
        })
        n += 1

    return txs


# ══════════════════════════════════════════════════════════════════
# SUSPICIOUS SCENARIO GENERATION
# ══════════════════════════════════════════════════════════════════

def scenario_rapid_redistribution() -> List[Dict]:
    """
    SCENARIO-001 (PRIMARY DEMO):
    A → B ₹10,00,000 at 10:04
    B → C ₹3,20,000 at 10:21 (new recipient)
    B → D ₹2,80,000 at 10:36 (new recipient)
    B → E ₹1,70,000 at 10:52
    B → F ₹2,00,000 at 11:02 (new recipient)
    E → G ₹1,40,000 at 11:18 (downstream)
    conservation_ratio = 9,70,000 / 10,00,000 = 0.97
    time_to_90pct_outflow ≈ 58 minutes
    """
    base = DEMO_DAY
    SCENARIO_ID = "SCENARIO-001"
    PAT = "synthetic_suspicious_pattern"
    txs = [
        {   # Inflow: A → B ₹10,00,000
            "transaction_id": "TXN-DEMO-S001-001",
            "timestamp": (base + timedelta(minutes=4)).isoformat(),
            "sender_account_id": "ACC-A-001",
            "receiver_account_id": "ACC-B-001",
            "amount": 1000000.00,
            "currency": "INR", "channel": "RTGS",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Mumbai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
        {   # Outflow 1: B → C ₹3,20,000 (new recipient)
            "transaction_id": "TXN-DEMO-S001-002",
            "timestamp": (base + timedelta(minutes=21)).isoformat(),
            "sender_account_id": "ACC-B-001",
            "receiver_account_id": "ACC-C-001",
            "amount": 320000.00,
            "currency": "INR", "channel": "IMPS",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Mumbai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
        {   # Outflow 2: B → D ₹2,80,000 (new recipient)
            "transaction_id": "TXN-DEMO-S001-003",
            "timestamp": (base + timedelta(minutes=36)).isoformat(),
            "sender_account_id": "ACC-B-001",
            "receiver_account_id": "ACC-D-001",
            "amount": 280000.00,
            "currency": "INR", "channel": "NEFT",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Delhi",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
        {   # Outflow 3: B → E ₹1,70,000
            "transaction_id": "TXN-DEMO-S001-004",
            "timestamp": (base + timedelta(minutes=52)).isoformat(),
            "sender_account_id": "ACC-B-001",
            "receiver_account_id": "ACC-E-001",
            "amount": 170000.00,
            "currency": "INR", "channel": "UPI",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Mumbai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
        {   # Outflow 4: B → F ₹2,00,000 (new recipient)
            "transaction_id": "TXN-DEMO-S001-005",
            "timestamp": (base + timedelta(minutes=62)).isoformat(),
            "sender_account_id": "ACC-B-001",
            "receiver_account_id": "ACC-F-001",
            "amount": 200000.00,
            "currency": "INR", "channel": "IMPS",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Bangalore",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
        {   # Downstream: E → G ₹1,40,000
            "transaction_id": "TXN-DEMO-S001-006",
            "timestamp": (base + timedelta(minutes=78)).isoformat(),
            "sender_account_id": "ACC-E-001",
            "receiver_account_id": "ACC-G-001",
            "amount": 140000.00,
            "currency": "INR", "channel": "UPI",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Chennai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        },
    ]
    return txs


def scenario_new_recipient_burst(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-002: Account rapidly sends to 8 new counterparties in 2 hours."""
    SCENARIO_ID = "SCENARIO-002"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    sender = regular[10]  # deterministic pick
    recipients = regular[50:58]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [sender] + list(recipients)
    base = DEMO_DAY - timedelta(days=3, hours=5)

    txs = []
    for i, rcv in enumerate(recipients):
        txs.append({
            "transaction_id": f"TXN-S002-{i+1:03d}",
            "timestamp": (base + timedelta(minutes=15*i)).isoformat(),
            "sender_account_id": sender,
            "receiver_account_id": rcv,
            "amount": round(random.uniform(20000, 80000), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Mumbai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [sender]


def scenario_fan_in(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-003: 6 accounts aggregate into one recipient."""
    SCENARIO_ID = "SCENARIO-003"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    receiver = regular[20]
    senders = regular[60:66]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [receiver] + list(senders)
    base = DEMO_DAY - timedelta(days=5, hours=2)

    txs = []
    for i, snd in enumerate(senders):
        txs.append({
            "transaction_id": f"TXN-S003-{i+1:03d}",
            "timestamp": (base + timedelta(hours=i*2)).isoformat(),
            "sender_account_id": snd,
            "receiver_account_id": receiver,
            "amount": round(random.uniform(50000, 150000), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Delhi",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [receiver]


def scenario_fan_out(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-004: One account sends to 10 recipients rapidly."""
    SCENARIO_ID = "SCENARIO-004"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    sender = regular[30]
    recipients = regular[70:80]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [sender] + list(recipients)
    base = DEMO_DAY - timedelta(days=7, hours=3)

    txs = []
    for i, rcv in enumerate(recipients):
        txs.append({
            "transaction_id": f"TXN-S004-{i+1:03d}",
            "timestamp": (base + timedelta(minutes=10*i)).isoformat(),
            "sender_account_id": sender,
            "receiver_account_id": rcv,
            "amount": round(random.uniform(30000, 60000), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Bangalore",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [sender]


def scenario_multihop(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-005: A→B→C→D→E multi-hop chain."""
    SCENARIO_ID = "SCENARIO-005"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    chain = regular[80:85]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = chain
    base = DEMO_DAY - timedelta(days=10, hours=6)
    amount = 300000.0

    txs = []
    for i in range(len(chain) - 1):
        txs.append({
            "transaction_id": f"TXN-S005-{i+1:03d}",
            "timestamp": (base + timedelta(hours=i*3)).isoformat(),
            "sender_account_id": chain[i],
            "receiver_account_id": chain[i+1],
            "amount": round(amount * (0.95 ** i), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Chennai",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [chain[0]]


def scenario_unusual_amount(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-006: Student account receives ₹50 lakh unusually."""
    SCENARIO_ID = "SCENARIO-006"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[accounts["expected_activity_category"] == "student"]["account_id"].tolist()
    receiver = regular[5]
    sender = accounts[accounts["expected_activity_category"] == "small_business"]["account_id"].tolist()[3]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [sender, receiver]
    base = DEMO_DAY - timedelta(days=2, hours=8)

    txs = [{
        "transaction_id": "TXN-S006-001",
        "timestamp": base.isoformat(),
        "sender_account_id": sender,
        "receiver_account_id": receiver,
        "amount": 5000000.00,
        "currency": "INR", "channel": "RTGS",
        "transaction_type": "transfer",
        "merchant_category": None, "location": "Hyderabad",
        "status": "completed",
        "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
    }]
    return txs, [receiver]


def scenario_behavioral_deviation(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-007: Salary account suddenly sends 50x its usual amount."""
    SCENARIO_ID = "SCENARIO-007"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[accounts["expected_activity_category"] == "salary"]["account_id"].tolist()
    sender = regular[15]
    receiver = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()[90]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [sender]
    base = DEMO_DAY - timedelta(days=1, hours=4)

    txs = [{
        "transaction_id": "TXN-S007-001",
        "timestamp": base.isoformat(),
        "sender_account_id": sender,
        "receiver_account_id": receiver,
        "amount": 2500000.00,  # 50x normal for salary account
        "currency": "INR", "channel": "NEFT",
        "transaction_type": "transfer",
        "merchant_category": None, "location": "Pune",
        "status": "completed",
        "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
    }]
    return txs, [sender]


def scenario_temporal_burst(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-008: 15 transactions in 30 minutes (velocity burst)."""
    SCENARIO_ID = "SCENARIO-008"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    sender = regular[100]
    recipients = regular[110:125]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [sender] + list(recipients)
    base = DEMO_DAY - timedelta(days=4, hours=2)

    txs = []
    for i, rcv in enumerate(recipients):
        txs.append({
            "transaction_id": f"TXN-S008-{i+1:03d}",
            "timestamp": (base + timedelta(minutes=2*i)).isoformat(),
            "sender_account_id": sender,
            "receiver_account_id": rcv,
            "amount": round(random.uniform(5000, 20000), 2),
            "currency": "INR", "channel": "UPI",
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Kolkata",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [sender]


def scenario_combined(accounts: pd.DataFrame) -> Tuple[List[Dict], List[str]]:
    """SCENARIO-009: Combined pattern — fan-in then rapid redistribution."""
    SCENARIO_ID = "SCENARIO-009"
    PAT = "synthetic_suspicious_pattern"
    regular = accounts[~accounts["is_synthetic_suspicious"]]["account_id"].tolist()
    hub = regular[130]
    senders = regular[140:145]
    recipients = regular[150:155]
    SCENARIO_ACCOUNTS[SCENARIO_ID] = [hub] + senders + recipients
    base = DEMO_DAY - timedelta(days=6, hours=12)

    txs = []
    # Fan-in phase
    for i, snd in enumerate(senders):
        txs.append({
            "transaction_id": f"TXN-S009-IN-{i+1:03d}",
            "timestamp": (base + timedelta(hours=i)).isoformat(),
            "sender_account_id": snd,
            "receiver_account_id": hub,
            "amount": round(random.uniform(100000, 200000), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Ahmedabad",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    # Fan-out phase
    for i, rcv in enumerate(recipients):
        txs.append({
            "transaction_id": f"TXN-S009-OUT-{i+1:03d}",
            "timestamp": (base + timedelta(hours=6, minutes=30*i)).isoformat(),
            "sender_account_id": hub,
            "receiver_account_id": rcv,
            "amount": round(random.uniform(80000, 160000), 2),
            "currency": "INR", "channel": random_channel(),
            "transaction_type": "transfer",
            "merchant_category": None, "location": "Ahmedabad",
            "status": "completed",
            "scenario_id": SCENARIO_ID, "ground_truth_pattern": PAT,
        })
    return txs, [hub]


# ══════════════════════════════════════════════════════════════════
# GROUND TRUTH
# ══════════════════════════════════════════════════════════════════

def build_ground_truth(suspicious_accounts: Dict[str, List[str]]) -> pd.DataFrame:
    """Build ground truth labels for evaluation."""
    records = []
    for scenario_id, accs in suspicious_accounts.items():
        for acc in accs:
            records.append({
                "scenario_id": scenario_id,
                "account_id": acc,
                "ground_truth_pattern": "synthetic_suspicious_pattern",
                "is_primary_subject": acc in [
                    "ACC-B-001", *[v[0] for v in list(suspicious_accounts.values()) if v]
                ],
            })
    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    print("[*] LaundraLens X - Synthetic Data Generator")
    print(f"    Seed: {DEMO_SEED} | Accounts: {N_ACCOUNTS} | Normal TXN: {N_NORMAL_TRANSACTIONS}")
    print()

    # 1. Generate accounts
    print("[1] Generating accounts...")
    accounts_df = generate_accounts()
    customers_df = generate_customers(accounts_df)
    print(f"    OK: {len(accounts_df)} accounts | {len(customers_df)} customers")

    # 2. Normal transactions
    print("[2] Generating normal transactions...")
    normal_txs = generate_normal_transactions(accounts_df)
    print(f"    OK: {len(normal_txs)} normal transactions")

    # 3. Suspicious scenarios
    print("[3] Generating suspicious scenarios...")
    suspicious_accounts: Dict[str, List[str]] = {
        "SCENARIO-001": ["ACC-B-001", "ACC-A-001"]
    }

    all_suspicious_txs = scenario_rapid_redistribution()  # S001
    print(f"    S001 (Rapid Redistribution): {len(all_suspicious_txs)} txns")

    s2_txs, s2_accs = scenario_new_recipient_burst(accounts_df)
    all_suspicious_txs += s2_txs
    suspicious_accounts["SCENARIO-002"] = s2_accs
    print(f"    S002 (New Recipient Burst): {len(s2_txs)} txns")

    s3_txs, s3_accs = scenario_fan_in(accounts_df)
    all_suspicious_txs += s3_txs
    suspicious_accounts["SCENARIO-003"] = s3_accs
    print(f"    S003 (Fan-In): {len(s3_txs)} txns")

    s4_txs, s4_accs = scenario_fan_out(accounts_df)
    all_suspicious_txs += s4_txs
    suspicious_accounts["SCENARIO-004"] = s4_accs
    print(f"    S004 (Fan-Out): {len(s4_txs)} txns")

    s5_txs, s5_accs = scenario_multihop(accounts_df)
    all_suspicious_txs += s5_txs
    suspicious_accounts["SCENARIO-005"] = s5_accs
    print(f"    S005 (Multi-Hop): {len(s5_txs)} txns")

    s6_txs, s6_accs = scenario_unusual_amount(accounts_df)
    all_suspicious_txs += s6_txs
    suspicious_accounts["SCENARIO-006"] = s6_accs
    print(f"    S006 (Unusual Amount): {len(s6_txs)} txns")

    s7_txs, s7_accs = scenario_behavioral_deviation(accounts_df)
    all_suspicious_txs += s7_txs
    suspicious_accounts["SCENARIO-007"] = s7_accs
    print(f"    S007 (Behavioral Deviation): {len(s7_txs)} txns")

    s8_txs, s8_accs = scenario_temporal_burst(accounts_df)
    all_suspicious_txs += s8_txs
    suspicious_accounts["SCENARIO-008"] = s8_accs
    print(f"    S008 (Temporal Burst): {len(s8_txs)} txns")

    s9_txs, s9_accs = scenario_combined(accounts_df)
    all_suspicious_txs += s9_txs
    suspicious_accounts["SCENARIO-009"] = s9_accs
    print(f"   S009 (Combined): {len(s9_txs)} txns")

    # 4. Combine + sort transactions
    all_txs = normal_txs + all_suspicious_txs
    txs_df = pd.DataFrame(all_txs)
    txs_df["timestamp"] = pd.to_datetime(txs_df["timestamp"])
    txs_df = txs_df.sort_values("timestamp").reset_index(drop=True)
    print(f"\n   ✅ Total: {len(txs_df)} transactions")

    # 5. Ground truth
    gt_df = build_ground_truth(suspicious_accounts)
    print(f"   ✅ {len(gt_df)} ground truth labels across {len(suspicious_accounts)} scenarios")

    # 6. Save
    out_dir = ROOT / "data" / "synthetic"
    out_dir.mkdir(parents=True, exist_ok=True)

    accounts_df.to_csv(out_dir / "accounts.csv", index=False)
    customers_df.to_csv(out_dir / "customers.csv", index=False)
    txs_df.to_csv(out_dir / "transactions.csv", index=False)
    gt_df.to_csv(out_dir / "ground_truth_scenarios.csv", index=False)

    print(f"\n✅ Data saved to {out_dir}/")
    print(f"   accounts.csv         → {len(accounts_df)} rows")
    print(f"   customers.csv        → {len(customers_df)} rows")
    print(f"   transactions.csv     → {len(txs_df)} rows")
    print(f"   ground_truth.csv     → {len(gt_df)} rows")
    print()
    print("🎯 Primary demo case: Account B (ACC-B-001) — SCENARIO-001")
    print("   conservation_ratio ≈ 0.97 (₹9,70,000 / ₹10,00,000)")
    print("   time_to_90pct_outflow ≈ 58 minutes")
    print("   new_recipient_ratio = 0.75 (3 of 4 recipients are new)")


if __name__ == "__main__":
    main()
