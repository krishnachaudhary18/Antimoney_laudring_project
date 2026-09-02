"""
LaundraLens X — Model Registry
Provides unified access to all trained models.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from src.models.xgboost_model import XGBoostDetector
from src.models.isolation_forest import IsolationForestDetector
from src.models.autoencoder import AutoencoderDetector

ROOT = Path(__file__).parent.parent.parent
ARTIFACTS_DIR = ROOT / "model_artifacts"


class ModelRegistry:
    """Singleton registry for all trained models."""

    _instance: Optional["ModelRegistry"] = None
    _loaded: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self.xgboost: Optional[XGBoostDetector] = None
        self.isolation_forest: Optional[IsolationForestDetector] = None
        self.autoencoder: Optional[AutoencoderDetector] = None
        self._loaded = False

    def load_all(self) -> Dict[str, bool]:
        """Load all model artifacts. Returns dict of model_name → loaded successfully."""
        status = {}

        # XGBoost
        xgb_dir = ARTIFACTS_DIR / "xgboost"
        if (xgb_dir / "model.pkl").exists():
            try:
                self.xgboost = XGBoostDetector.load(xgb_dir)
                status["xgboost"] = True
            except Exception as e:
                print(f"[WARN] XGBoost load failed: {e}")
                status["xgboost"] = False
        else:
            status["xgboost"] = False

        # Isolation Forest
        if_dir = ARTIFACTS_DIR / "isolation_forest"
        if (if_dir / "model.pkl").exists():
            try:
                self.isolation_forest = IsolationForestDetector.load(if_dir)
                status["isolation_forest"] = True
            except Exception as e:
                print(f"[WARN] Isolation Forest load failed: {e}")
                status["isolation_forest"] = False
        else:
            status["isolation_forest"] = False

        # Autoencoder
        ae_dir = ARTIFACTS_DIR / "autoencoder"
        if (ae_dir / "metadata.json").exists():
            try:
                self.autoencoder = AutoencoderDetector.load(ae_dir)
                status["autoencoder"] = True
            except Exception as e:
                print(f"[WARN] Autoencoder load failed: {e}")
                status["autoencoder"] = False
        else:
            status["autoencoder"] = False

        self._loaded = any(status.values())
        return status

    def score_all(self, feature_vector: list) -> Dict[str, float]:
        """
        Score a feature vector with all available models.
        Returns dict of model_name → normalized score [0,1].
        Falls back to 0.5 if model not available.
        """
        import numpy as np
        X = np.array(feature_vector, dtype=float)

        scores = {}

        if self.xgboost is not None:
            scores["xgboost_score"] = self.xgboost.predict_score(X)
        else:
            scores["xgboost_score"] = 0.5

        if self.isolation_forest is not None:
            scores["isolation_score"] = self.isolation_forest.predict_score(X)
        else:
            scores["isolation_score"] = 0.5

        if self.autoencoder is not None:
            scores["autoencoder_score"] = self.autoencoder.predict_score(X)
        else:
            scores["autoencoder_score"] = 0.5

        return scores

    def get_shap_values(self, feature_vector: list) -> Dict[str, float]:
        """Get SHAP values from XGBoost if available."""
        if self.xgboost is None:
            return {}
        import numpy as np
        X = np.array(feature_vector, dtype=float)
        return self.xgboost.get_shap_values(X) or {}

    @property
    def models_loaded(self) -> bool:
        return self._loaded


# Global singleton
registry = ModelRegistry()
