"""
LaundraLens X — Model Training Pipeline
Trains XGBoost, Isolation Forest, and Autoencoder on synthetic feature data.
Generates labeled feature matrix from all accounts using the feature pipeline.

Usage:
    python scripts/train_models.py
"""
from __future__ import annotations

import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from src.features.pipeline import compute_features, features_to_ml_vector, ML_FEATURE_NAMES
from src.features.network import build_transaction_graph
from src.models.xgboost_model import XGBoostDetector
from src.models.isolation_forest import IsolationForestDetector
from src.models.autoencoder import AutoencoderDetector

SYNTHETIC_DIR = ROOT / "data" / "synthetic"
ARTIFACTS_DIR = ROOT / "model_artifacts"
ALERT_TIMESTAMP = datetime(2026, 8, 14, 11, 30, 0)  # moment of alerts


def load_data():
    """Load synthetic data."""
    accounts_df = pd.read_csv(SYNTHETIC_DIR / "accounts.csv")
    txs_df = pd.read_csv(SYNTHETIC_DIR / "transactions.csv")
    gt_df = pd.read_csv(SYNTHETIC_DIR / "ground_truth_scenarios.csv")
    txs_df["timestamp"] = pd.to_datetime(txs_df["timestamp"])
    return accounts_df, txs_df, gt_df


def build_feature_matrix(accounts_df, txs_df, gt_df):
    """
    Compute feature vectors for all accounts.
    Labels: 1 if account appears in ground truth as suspicious, 0 otherwise.
    """
    print("[*] Building transaction graph...")
    G = build_transaction_graph(txs_df, alert_timestamp=ALERT_TIMESTAMP)
    print(f"    Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    suspicious_accounts = set(gt_df["account_id"].tolist())
    account_ids = accounts_df["account_id"].tolist()

    print(f"[*] Computing features for {len(account_ids)} accounts...")
    X_list = []
    y_list = []
    account_id_list = []

    for i, acc_id in enumerate(account_ids):
        if i % 100 == 0:
            print(f"    Progress: {i}/{len(account_ids)}")
        try:
            features = compute_features(
                account_id=acc_id,
                transactions_df=txs_df,
                alert_timestamp=ALERT_TIMESTAMP,
                graph=G,
                suspicious_account_ids=list(suspicious_accounts),
            )
            vec = features_to_ml_vector(features)
            X_list.append(vec)
            y_list.append(1 if acc_id in suspicious_accounts else 0)
            account_id_list.append(acc_id)
        except Exception as e:
            # Use zero vector if feature computation fails
            X_list.append([0.0] * len(ML_FEATURE_NAMES))
            y_list.append(1 if acc_id in suspicious_accounts else 0)
            account_id_list.append(acc_id)

    X = np.array(X_list, dtype=float)
    y = np.array(y_list, dtype=int)

    # Handle NaN/Inf
    X = np.nan_to_num(X, nan=0.0, posinf=1.0, neginf=0.0)

    print(f"    Feature matrix: {X.shape} | Suspicious: {y.sum()} / {len(y)}")
    return X, y, np.array(account_id_list), G


def train_xgboost(X, y):
    """Train and evaluate XGBoost."""
    print("\n[1] Training XGBoost...")
    detector = XGBoostDetector(ARTIFACTS_DIR / "xgboost")
    metrics = detector.train(X, y, feature_names=ML_FEATURE_NAMES)
    detector.save()
    print(f"    Metrics: precision={metrics.get('precision', 'N/A')} | "
          f"recall={metrics.get('recall', 'N/A')} | "
          f"F1={metrics.get('f1', 'N/A')} | "
          f"ROC-AUC={metrics.get('roc_auc', 'N/A')}")
    return detector, metrics


def train_isolation_forest(X):
    """Train Isolation Forest on all accounts."""
    print("\n[2] Training Isolation Forest...")
    detector = IsolationForestDetector(ARTIFACTS_DIR / "isolation_forest")
    metrics = detector.train(X, contamination=0.05)
    detector.save()
    print(f"    Anomalies detected: {metrics['n_anomalies_detected']} / {metrics['n_samples']}")
    return detector, metrics


def train_autoencoder(X, y):
    """Train Autoencoder on normal accounts only."""
    print("\n[3] Training Autoencoder (normal accounts only)...")
    # Train only on normal accounts to learn normal behavior
    X_normal = X[y == 0]
    print(f"    Normal samples: {len(X_normal)}")

    detector = AutoencoderDetector(ARTIFACTS_DIR / "autoencoder")
    metrics = detector.train(X_normal, epochs=50, batch_size=64)
    detector.save()

    if metrics.get("fallback"):
        print(f"    [!] Autoencoder fallback active: {metrics.get('reason', 'unknown')}")
        print(f"    Fallback: autoencoder_score will return 0.5 (neutral) for all predictions.")
    else:
        print(f"    Final loss: {metrics.get('final_loss', 'N/A')}")
    return detector, metrics


def verify_demo_scores(xgb_detector, if_detector, ae_detector, X, account_id_list):
    """Verify that the demo account ACC-B-001 scores HIGH/CRITICAL."""
    print("\n[*] Verifying demo account scores (ACC-B-001)...")
    idx = list(account_id_list).index("ACC-B-001") if "ACC-B-001" in account_id_list else -1
    if idx == -1:
        print("    [!] ACC-B-001 not found in feature matrix")
        return

    x = X[idx]
    xgb_score = xgb_detector.predict_score(x)
    if_score = if_detector.predict_score(x)
    ae_score = ae_detector.predict_score(x)

    print(f"    ACC-B-001 XGBoost score:        {xgb_score:.3f}")
    print(f"    ACC-B-001 Isolation Forest:     {if_score:.3f}")
    print(f"    ACC-B-001 Autoencoder:          {ae_score:.3f}")

    # Simple risk fusion preview
    ensemble_score = 0.40 * xgb_score + 0.30 * if_score + 0.30 * ae_score
    print(f"    ACC-B-001 Ensemble preview:     {ensemble_score:.3f}")
    if ensemble_score > 0.6:
        print("    [OK] Demo account correctly flagged as HIGH/CRITICAL risk")
    else:
        print("    [WARN] Demo account score lower than expected — check feature computation")


def save_summary(xgb_metrics, if_metrics, ae_metrics):
    """Save training summary."""
    summary = {
        "trained_at": datetime.utcnow().isoformat(),
        "xgboost": xgb_metrics,
        "isolation_forest": if_metrics,
        "autoencoder": ae_metrics,
        "note": "Evaluation uses synthetic/anonymized demonstration data. Does not represent production financial-crime performance.",
    }
    with open(ARTIFACTS_DIR / "training_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\nTraining summary saved to {ARTIFACTS_DIR}/training_summary.json")


def main():
    print("=" * 60)
    print("LaundraLens X -- Model Training Pipeline")
    print("=" * 60)
    print()
    print("NOTE: Evaluation uses synthetic/anonymized data only.")
    print("      Does not represent production financial-crime detection.")
    print()

    # Load
    accounts_df, txs_df, gt_df = load_data()

    # Features
    X, y, account_id_list, G = build_feature_matrix(accounts_df, txs_df, gt_df)

    # Train all 3 models
    xgb_detector, xgb_metrics = train_xgboost(X, y)
    if_detector, if_metrics = train_isolation_forest(X)
    ae_detector, ae_metrics = train_autoencoder(X, y)

    # Verify demo case
    verify_demo_scores(xgb_detector, if_detector, ae_detector, X, account_id_list)

    # Save summary
    save_summary(xgb_metrics, if_metrics, ae_metrics)

    print()
    print("=" * 60)
    print("Training complete.")
    print("Run: uvicorn src.api.main:app --reload")
    print("     streamlit run dashboard/app.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
