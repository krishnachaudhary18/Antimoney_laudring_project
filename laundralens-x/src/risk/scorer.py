"""
LaundraLens X — Risk Fusion Engine
Combines all model scores and deterministic signals into
the final Investigation Priority Score (0-100).

Named: "Investigation Priority Score" (never "probability of crime").
"""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, Optional

import numpy as np

ROOT = Path(__file__).parent.parent.parent
RISK_CONFIG = ROOT / "config" / "risk_config.yaml"


def load_weights() -> Dict[str, float]:
    """Load risk fusion weights from config."""
    try:
        with open(RISK_CONFIG) as f:
            cfg = yaml.safe_load(f)
        weights = cfg.get("weights", {})
    except Exception:
        weights = {}

    defaults = {
        "xgboost": 0.20,
        "isolation_forest": 0.10,
        "autoencoder": 0.10,
        "behavior": 0.15,
        "temporal": 0.15,
        "flow": 0.15,
        "graph": 0.15,
    }
    for k, v in defaults.items():
        if k not in weights:
            weights[k] = v

    # Normalize to sum to 1.0
    total = sum(weights.values())
    if total > 0:
        weights = {k: v / total for k, v in weights.items()}

    return weights


def get_risk_band(score: float) -> str:
    """Convert numeric score to risk band."""
    if score >= 80:
        return "CRITICAL"
    elif score >= 60:
        return "HIGH"
    elif score >= 30:
        return "MEDIUM"
    else:
        return "LOW"


def compute_risk_score(
    xgboost_score: float = 0.5,
    isolation_score: float = 0.5,
    autoencoder_score: float = 0.5,
    behavior_signal: float = 0.0,
    temporal_signal: float = 0.0,
    flow_signal: float = 0.0,
    graph_signal: float = 0.0,
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Compute weighted Investigation Priority Score.

    Formula: score = Σ(weight_i × normalized_signal_i) × 100

    All signals must be in [0,1].
    """
    weights = custom_weights or load_weights()

    signals = {
        "xgboost": float(np.clip(xgboost_score, 0.0, 1.0)),
        "isolation_forest": float(np.clip(isolation_score, 0.0, 1.0)),
        "autoencoder": float(np.clip(autoencoder_score, 0.0, 1.0)),
        "behavior": float(np.clip(behavior_signal, 0.0, 1.0)),
        "temporal": float(np.clip(temporal_signal, 0.0, 1.0)),
        "flow": float(np.clip(flow_signal, 0.0, 1.0)),
        "graph": float(np.clip(graph_signal, 0.0, 1.0)),
    }

    # Weighted sum
    raw_score = sum(weights.get(k, 0.0) * v for k, v in signals.items())
    priority_score = round(float(np.clip(raw_score * 100, 0.0, 100.0)), 1)
    risk_band = get_risk_band(priority_score)

    return {
        "priority_score": priority_score,
        "risk_band": risk_band,
        "signals": {k: round(v, 4) for k, v in signals.items()},
        "weights_used": {k: round(v, 4) for k, v in weights.items()},
        "label": "Investigation Priority Score",
        "disclaimer": (
            "This score reflects investigation priority based on multiple signals. "
            "It does not establish wrongdoing or confirm criminal activity. "
            "All findings require human review."
        ),
    }


def compute_counterfactual(
    base_signals: Dict[str, float],
    base_score: float,
) -> Dict[str, float]:
    """
    Score sensitivity: what would the score be without each signal?
    Shows signal contribution, not causal certainty.
    """
    weights = load_weights()
    sensitivity = {"baseline": round(base_score, 1)}

    for signal_name in ["flow", "graph", "behavior", "temporal", "xgboost", "autoencoder", "isolation_forest"]:
        # Zero out this signal
        modified = dict(base_signals)
        modified[signal_name] = 0.0

        # Recompute with zeroed signal
        raw = sum(weights.get(k, 0.0) * float(np.clip(v, 0.0, 1.0)) for k, v in modified.items())
        new_score = round(float(np.clip(raw * 100, 0.0, 100.0)), 1)
        sensitivity[f"without_{signal_name}"] = new_score

    return sensitivity
