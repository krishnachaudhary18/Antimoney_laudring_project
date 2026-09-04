"""
LaundraLens X — Canonical Investigation & Risk Snapshot Architecture
Provides a single canonical data structure for completed investigations.
Guarantees consistent risk scores, model scores, evidence, and reports across all pages.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

ROOT = Path(__file__).parent.parent.parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"


@dataclass
class CaseRiskSnapshot:
    """Canonical risk outcome for a case, ensuring exact multi-view score consistency."""
    case_id: str
    alert_id: str
    account_id: str
    final_score: float
    risk_band: str
    behavior_signal: float
    temporal_signal: float
    flow_signal: float
    graph_signal: float
    model_scores: Dict[str, float]
    generated_at: str
    model_version: str = "1.0.0"
    feature_version: str = "1.0.0"
    random_seed: int = 42

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InvestigationSnapshot:
    """Complete canonical snapshot for an investigation."""
    case_id: str
    alert_id: str
    account_id: str
    status: str
    final_score: float
    risk_band: str
    deterministic_signals: Dict[str, float]
    signal_metrics: Dict[str, Any]
    model_scores: Dict[str, float]
    account_profile: Dict[str, Any] = field(default_factory=dict)
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    behavioral_features: Dict[str, Any] = field(default_factory=dict)
    temporal_features: Dict[str, Any] = field(default_factory=dict)
    flow_features: Dict[str, Any] = field(default_factory=dict)
    network_features: Dict[str, Any] = field(default_factory=dict)
    graph: Dict[str, Any] = field(default_factory=dict)
    lineage: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)
    timeline: Dict[str, Any] = field(default_factory=dict)
    explanation: Dict[str, Any] = field(default_factory=dict)
    sensitivity: Dict[str, Any] = field(default_factory=dict)
    report: Dict[str, Any] = field(default_factory=dict)
    duration_seconds: float = 1.2
    feature_version: str = "1.0.0"
    model_version: str = "1.0.0"
    random_seed: int = 42
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_risk_snapshot(self) -> CaseRiskSnapshot:
        return CaseRiskSnapshot(
            case_id=self.case_id,
            alert_id=self.alert_id,
            account_id=self.account_id,
            final_score=self.final_score,
            risk_band=self.risk_band,
            behavior_signal=self.deterministic_signals.get("behavior", 0.0),
            temporal_signal=self.deterministic_signals.get("temporal", 0.0),
            flow_signal=self.deterministic_signals.get("flow", 0.0),
            graph_signal=self.deterministic_signals.get("graph", 0.0),
            model_scores=self.model_scores,
            generated_at=self.generated_at,
            model_version=self.model_version,
            feature_version=self.feature_version,
            random_seed=self.random_seed,
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Compatibility aliases for existing UI and API callers
        d["priority_score"] = self.final_score
        d["signals"] = self.deterministic_signals
        d["shap_contributions"] = self.explanation.get("shap_contributions", {})
        d["counterfactual"] = self.sensitivity.get("counterfactual", {})
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InvestigationSnapshot:
        score = data.get("final_score", data.get("priority_score", 0.0))
        signals = data.get("deterministic_signals", data.get("signals", {}))
        return cls(
            case_id=data["case_id"],
            alert_id=data.get("alert_id", ""),
            account_id=data.get("account_id", ""),
            status=data.get("status", "REPORT_READY"),
            final_score=float(score),
            risk_band=data.get("risk_band", "LOW"),
            deterministic_signals=signals,
            signal_metrics=data.get("signal_metrics", {}),
            model_scores=data.get("model_scores", {}),
            account_profile=data.get("account_profile", {}),
            transactions=data.get("transactions", []),
            behavioral_features=data.get("behavioral_features", {}),
            temporal_features=data.get("temporal_features", {}),
            flow_features=data.get("flow_features", {}),
            network_features=data.get("network_features", {}),
            graph=data.get("graph", {}),
            lineage=data.get("lineage", {}),
            evidence=data.get("evidence", []),
            findings=data.get("findings", []),
            timeline=data.get("timeline", {}),
            explanation=data.get("explanation", {}),
            sensitivity=data.get("sensitivity", {}),
            report=data.get("report", {}),
            duration_seconds=data.get("duration_seconds", 1.0),
            feature_version=data.get("feature_version", "1.0.0"),
            model_version=data.get("model_version", "1.0.0"),
            random_seed=data.get("random_seed", 42),
            generated_at=data.get("generated_at", datetime.now(timezone.utc).isoformat()),
        )


def get_snapshot_path(case_id: str) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR / f"{case_id}.json"


def save_snapshot(snapshot: InvestigationSnapshot) -> Path:
    """Persist the canonical investigation snapshot to disk."""
    p = get_snapshot_path(snapshot.case_id)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(snapshot.to_dict(), f, indent=2, default=str)
    return p


def load_snapshot(case_id: str) -> Optional[InvestigationSnapshot]:
    """Load a persisted snapshot for a given case_id."""
    p = get_snapshot_path(case_id)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return InvestigationSnapshot.from_dict(data)
    except Exception:
        return None
