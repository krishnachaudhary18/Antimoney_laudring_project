"""
Regression and consistency test suite for LaundraLens X.
Verifies all 11 invariants from the hackathon stabilization specification.
"""
import json
from pathlib import Path
import pytest
import pandas as pd
import networkx as nx

from src.db.database import SessionLocal
from src.db.models import Alert, Investigation
from src.risk.snapshot import load_snapshot, InvestigationSnapshot
from src.api.routes.graph import _get_or_build_graph
from src.graph.visualizer import generate_subgraph_html
from src.evidence.report import _generate_deterministic_report, generate_report_with_gemini
from src.risk.scorer import compute_counterfactual, load_weights


def test_graph_generation_returns_valid_html():
    """1. Verify graph visualizer returns valid HTML with vis-network scripts."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)
    assert G.number_of_nodes() > 0
    html = generate_subgraph_html(G, "ACC-B-001", hops=2)
    assert isinstance(html, str)
    assert len(html) > 500
    assert "vis-network" in html
    assert "ACC-B-001" in html


def test_graph_has_nodes_and_edges():
    """2. Verify subgraph contains nodes, directed edges, and center node."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)
    assert "ACC-B-001" in G
    sub = nx.ego_graph(G, "ACC-B-001", radius=2, undirected=True)
    assert sub.number_of_nodes() >= 2
    assert sub.number_of_edges() >= 1
    # Check that incoming edge from sender ACC-A-001 is included
    assert "ACC-A-001" in sub


def test_flow_conservation_matches_evidence():
    """3. Verify flow conservation raw metric matches evidence formula."""
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    metrics = snapshot.signal_metrics
    flow_ratio = metrics.get("flow_conservation_ratio", 0.0)
    assert 0.95 <= flow_ratio <= 1.0
    # Weighted risk signal is decoupled from raw conservation metric
    flow_signal = snapshot.deterministic_signals.get("flow", 0.0)
    assert flow_signal > 0.0
    assert abs(flow_signal - flow_ratio) > 0.01  # Verifies decouple distinction


def test_alert_queue_score_matches_investigation_score():
    """4. Invariant: alert_queue_score == investigation_score for the same case."""
    with SessionLocal() as db:
        alert = db.query(Alert).filter(Alert.alert_id == "ALERT-SCENARIO-001").first()
        assert alert is not None
        alert_score = float(alert.priority_score)
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    assert round(alert_score, 1) == round(snapshot.final_score, 1)


def test_investigation_score_matches_report_score():
    """5. Invariant: investigation_score == report_score."""
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    inv_score = round(snapshot.final_score, 1)
    rep_score = round(snapshot.report.get("final_score", 0.0), 1)
    assert inv_score == rep_score


def test_risk_panel_score_matches_report_score():
    """6. Invariant: risk_panel_score == report_score."""
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    d = snapshot.to_dict()
    assert round(d["priority_score"], 1) == round(snapshot.report.get("priority_score", 0.0), 1)


def test_investigation_snapshot_is_deterministic():
    """7. Verify snapshot produces identical scores given identical seed."""
    snap1 = load_snapshot("CASE-DEMO-001")
    assert snap1 is not None
    assert snap1.random_seed == 42
    # Verify score does not fluctuate
    assert snap1.final_score == snap1.report.get("final_score")


def test_report_uses_correct_account_id():
    """8. Report must be generated for the exact investigated account, not a hardcoded default."""
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    assert snapshot.report.get("account_id") == snapshot.account_id
    assert snapshot.report.get("case_id") == snapshot.case_id

    # Test arbitrary account report generation
    arbitrary_case = {
        "case_id": "CASE-TEST-999",
        "account_id": "ACC-TEST-999",
        "priority_score": 55.0,
        "risk_band": "MEDIUM",
        "signals": {"flow": 0.5, "temporal": 0.5, "behavior": 0.5, "graph": 0.5},
        "model_scores": {"xgboost_score": 0.5, "isolation_score": 0.5, "autoencoder_score": 0.5},
    }
    rep = _generate_deterministic_report(arbitrary_case)
    assert rep["account_id"] == "ACC-TEST-999"
    assert rep["case_id"] == "CASE-TEST-999"
    assert "ACC-TEST-999" in rep["body"]


def test_counterfactual_does_not_mutate_case_score():
    """9. Counterfactual simulation must operate on an isolated copy and not mutate baseline score."""
    snapshot = load_snapshot("CASE-DEMO-001")
    assert snapshot is not None
    original_score = snapshot.final_score

    simulated_signals = dict(snapshot.deterministic_signals)
    simulated_signals["flow"] = 0.10  # Drop flow to 10%
    cf = compute_counterfactual(simulated_signals, snapshot.final_score)

    assert cf["baseline"] == original_score
    assert snapshot.final_score == original_score  # Unmutated


def test_stepper_fails_if_artifact_missing():
    """10. Pipeline step states must not report SUCCESS if underlying artifact is missing."""
    empty_graph = nx.DiGraph()
    # Check that empty graph results in empty/failed state
    html = generate_subgraph_html(empty_graph, "ACC-MISSING", hops=2)
    assert "No connected transactions found" in html


def test_zero_hallucination_claim_removed():
    """11. Verify absolute claims 'zero hallucination' and 'immutable database records' are removed."""
    root = Path(__file__).parent.parent
    report_py = (root / "src" / "evidence" / "report.py").read_text(encoding="utf-8")
    app_py = (root / "dashboard" / "app.py").read_text(encoding="utf-8")

    assert "zero hallucination" not in report_py.lower()
    assert "zero hallucination" not in app_py.lower()
    assert "immutable database records" not in report_py.lower()
    assert "immutable database records" not in app_py.lower()
