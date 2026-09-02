"""
LaundraLens X — Score Sensitivity / Counterfactual Analysis
Simulates 'What-If' scenarios showing how changing signals impacts the composite score.
"""
from __future__ import annotations

from typing import Dict, Any
from src.risk.scorer import compute_risk_score


class CounterfactualAnalyzer:
    @staticmethod
    def analyze_sensitivity(base_signals: Dict[str, float], model_scores: Dict[str, float]) -> Dict[str, float]:
        """Compute impact of nullifying individual components."""
        base_res = compute_risk_score(
            xgboost_score=model_scores.get("xgboost_score", 0.5),
            isolation_score=model_scores.get("isolation_score", 0.5),
            autoencoder_score=model_scores.get("autoencoder_score", 0.5),
            behavior_signal=base_signals.get("behavior", 0.0),
            temporal_signal=base_signals.get("temporal", 0.0),
            flow_signal=base_signals.get("flow", 0.0),
            graph_signal=base_signals.get("graph", 0.0),
        )
        base_score = base_res["priority_score"]

        results = {"baseline": base_score}

        # Test zeroing each signal
        for sig in ["flow", "temporal", "behavior", "graph"]:
            modified = dict(base_signals)
            modified[sig] = 0.0
            res = compute_risk_score(
                xgboost_score=model_scores.get("xgboost_score", 0.5),
                isolation_score=model_scores.get("isolation_score", 0.5),
                autoencoder_score=model_scores.get("autoencoder_score", 0.5),
                behavior_signal=modified.get("behavior", 0.0),
                temporal_signal=modified.get("temporal", 0.0),
                flow_signal=modified.get("flow", 0.0),
                graph_signal=modified.get("graph", 0.0),
            )
            results[f"without_{sig}"] = res["priority_score"]

        return results
