"""
LaundraLens X — Isolation Forest Anomaly Detector
Unsupervised detection without relying on labels.
Normalized score: larger value = more anomalous.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class IsolationForestDetector:
    """Unsupervised anomaly detector using Isolation Forest."""

    def __init__(self, artifact_dir: Path):
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._score_min: float = -1.0
        self._score_max: float = 0.0

    def train(self, X: np.ndarray, contamination: float = 0.05) -> dict:
        """
        Train Isolation Forest on all accounts (no labels needed).
        contamination = expected fraction of anomalies (conservative: 5%).
        """
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)

        # Calibrate score range on training data
        raw_scores = self.model.score_samples(X_scaled)  # negative: lower = more anomalous
        self._score_min = float(raw_scores.min())
        self._score_max = float(raw_scores.max())

        n_anomalies = int((self.model.predict(X_scaled) == -1).sum())
        return {
            "n_samples": len(X),
            "n_anomalies_detected": n_anomalies,
            "contamination": contamination,
            "score_range": [round(self._score_min, 4), round(self._score_max, 4)],
        }

    def predict_score(self, X: np.ndarray) -> float:
        """
        Return normalized anomaly score [0,1].
        0 = normal, 1 = maximally anomalous.
        """
        if self.model is None or self.scaler is None:
            return 0.5
        X_scaled = self.scaler.transform(X.reshape(1, -1))
        raw = float(self.model.score_samples(X_scaled)[0])

        # Normalize: lower raw score = more anomalous → invert to [0,1]
        score_range = self._score_max - self._score_min
        if score_range < 1e-8:
            return 0.5
        normalized = (self._score_max - raw) / score_range
        return round(float(np.clip(normalized, 0.0, 1.0)), 4)

    def save(self):
        with open(self.artifact_dir / "model.pkl", "wb") as f:
            pickle.dump(self.model, f)
        with open(self.artifact_dir / "scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)
        meta = {
            "score_min": self._score_min,
            "score_max": self._score_max,
        }
        with open(self.artifact_dir / "metadata.json", "w") as f:
            json.dump(meta, f, indent=2)
        print(f"    Isolation Forest artifacts saved to {self.artifact_dir}/")

    @classmethod
    def load(cls, artifact_dir: Path) -> "IsolationForestDetector":
        detector = cls(artifact_dir)
        with open(artifact_dir / "model.pkl", "rb") as f:
            detector.model = pickle.load(f)
        with open(artifact_dir / "scaler.pkl", "rb") as f:
            detector.scaler = pickle.load(f)
        meta_path = artifact_dir / "metadata.json"
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
            detector._score_min = meta.get("score_min", -1.0)
            detector._score_max = meta.get("score_max", 0.0)
        return detector
