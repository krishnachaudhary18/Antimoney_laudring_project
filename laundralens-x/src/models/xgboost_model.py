"""
LaundraLens X — XGBoost Supervised Detection Model
Trained on synthetic labeled data with SHAP explainability.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    classification_report,
)
import xgboost as xgb

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class XGBoostDetector:
    """Supervised XGBoost classifier for AML detection with SHAP explainability."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.explainer = None
        self.feature_names: List[str] = []
        self.eval_metrics: Dict = {}

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict:
        """
        Train XGBoost on labeled feature matrix.
        Uses time-aware split: last test_size fraction = test set.
        """
        self.feature_names = feature_names

        # Stratified train/test split to ensure realistic evaluation on both classes
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Scale
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Class weights for imbalanced data
        n_pos = max(int(y_train.sum()), 1)
        n_neg = len(y_train) - n_pos
        scale_pos_weight = n_neg / n_pos

        # XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_pos_weight,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=random_state,
            n_jobs=-1,
        )
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False,
        )

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_prob = self.model.predict_proba(X_test_scaled)[:, 1]

        metrics = {
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        }
        if len(np.unique(y_test)) > 1:
            metrics["roc_auc"] = round(float(roc_auc_score(y_test, y_prob)), 4)
            metrics["pr_auc"] = round(float(average_precision_score(y_test, y_prob)), 4)

        self.eval_metrics = metrics

        # SHAP explainer
        if SHAP_AVAILABLE:
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception:
                self.explainer = None

        return metrics

    def predict_score(self, X: np.ndarray) -> float:
        """Return normalized suspicious score [0,1] for a single sample."""
        if self.model is None or self.scaler is None:
            return 0.5  # neutral fallback
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        prob = float(self.model.predict_proba(X_scaled)[0, 1])
        return round(prob, 4)

    def get_shap_values(self, X: np.ndarray) -> Optional[Dict[str, float]]:
        """Return top SHAP feature contributions for a single sample."""
        if self.explainer is None or not SHAP_AVAILABLE:
            # Fallback: use native feature importance
            if self.model and self.feature_names:
                importances = self.model.feature_importances_
                top_idx = np.argsort(importances)[::-1][:10]
                return {
                    self.feature_names[i]: round(float(importances[i]), 4)
                    for i in top_idx
                }
            return {}

        try:
            if self.scaler:
                X_scaled = self.scaler.transform(X.reshape(1, -1))
            else:
                X_scaled = X.reshape(1, -1)
            shap_vals = self.explainer.shap_values(X_scaled)
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[1]  # positive class
            values = shap_vals[0]
            return {
                name: round(float(val), 4)
                for name, val in sorted(
                    zip(self.feature_names, values),
                    key=lambda x: abs(x[1]),
                    reverse=True,
                )[:15]
            }
        except Exception:
            return {}

    def save(self):
        """Persist model artifacts."""
        with open(self.artifact_dir / "model.pkl", "wb") as f:
            pickle.dump(self.model, f)
        with open(self.artifact_dir / "scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)
        if self.explainer is not None:
            with open(self.artifact_dir / "shap_explainer.pkl", "wb") as f:
                pickle.dump(self.explainer, f)
        # Save metadata
        meta = {
            "feature_names": self.feature_names,
            "eval_metrics": self.eval_metrics,
            "shap_available": self.explainer is not None,
        }
        import json
        with open(self.artifact_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"    XGBoost artifacts saved to {self.artifact_dir}/")

    @classmethod
    def load(cls, artifact_dir: Path) -> "XGBoostDetector":
        """Load persisted model."""
        detector = cls(artifact_dir)
        with open(artifact_dir / "model.pkl", "rb") as f:
            detector.model = pickle.load(f)
        with open(artifact_dir / "scaler.pkl", "rb") as f:
            detector.scaler = pickle.load(f)
        shap_path = artifact_dir / "shap_explainer.pkl"
        if shap_path.exists():
            with open(shap_path, "rb") as f:
                detector.explainer = pickle.load(f)
        import json
        meta_path = artifact_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            detector.feature_names = meta.get("feature_names", [])
            detector.eval_metrics = meta.get("eval_metrics", {})
        return detector
