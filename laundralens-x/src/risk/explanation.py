"""
LaundraLens X — Risk Explanation Engine
Synthesizes feature importances (SHAP), signal breakdowns, and human-readable narratives.
"""
from __future__ import annotations

from typing import Dict, List, Any


class RiskExplainer:
    """Translates numeric signals and ML outputs into plain-language analyst explanations."""

    @staticmethod
    def generate_narrative(signals: Dict[str, float], model_scores: Dict[str, float]) -> List[str]:
        narratives = []

        flow = signals.get("flow", 0.0)
        if flow >= 0.7:
            narratives.append("Critical Fund Conservation: Outflow volume closely tracks incoming funds within hours, a strong indicator of passthrough layering.")
        elif flow >= 0.4:
            narratives.append("Elevated Fund Conservation: Proportion of outgoing transfers is higher than typical baseline.")

        temporal = signals.get("temporal", 0.0)
        if temporal >= 0.6:
            narratives.append("Rapid Velocity Burst: Outgoing transactions initiated in compressed timeframe immediately following primary credit.")

        graph = signals.get("graph", 0.0)
        if graph >= 0.5:
            narratives.append("Network Dispersion: Counterparty hub behavior with high fan-out to newly observed counterparties.")

        xgb = model_scores.get("xgboost_score", 0.0)
        if xgb >= 0.8:
            narratives.append("Supervised Model Consensus: Pattern aligns closely with historical high-risk transaction clusters.")

        return narratives
