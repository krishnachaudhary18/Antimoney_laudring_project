"""
Unit tests for AI Investigation Orchestrator.
"""
from src.agents.orchestrator import InvestigationOrchestrator


def test_orchestrator_execution():
    orchestrator = InvestigationOrchestrator(
        case_id="TEST-CASE-001",
        alert_id="ALERT-SCENARIO-001",
        account_id="ACC-B-001",
    )
    result = orchestrator.run()

    assert result["status"] == "REPORT_READY"
    assert result["priority_score"] > 50.0
    assert result["findings_count"] >= 1
    assert result["evidence_count"] >= 1
    assert "signals" in result
    assert "timeline" in result
    assert "counterfactual" in result
    assert result["label"] == "Investigation Priority Score"
