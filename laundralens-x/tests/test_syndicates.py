"""
Unit tests for Multi-Account Syndicate & Mule Ring Forensics.
"""
import networkx as nx
from src.graph.syndicate import SyndicateForensics


def test_syndicate_cycle_detection():
    # Build a 3-node cycle: A -> B -> C -> A
    G = nx.DiGraph()
    G.add_edge("ACC-1", "ACC-2", weight=100000.0)
    G.add_edge("ACC-2", "ACC-3", weight=95000.0)
    G.add_edge("ACC-3", "ACC-1", weight=90000.0)

    res = SyndicateForensics.detect_syndicate_patterns(G, max_cycle_length=4)
    assert len(res["round_tripping_cycles"]) >= 1
    cycle = res["round_tripping_cycles"][0]
    assert cycle["length"] == 3
    assert cycle["cycle_volume"] > 0
    assert res["syndicate_risk_score"] > 0.0


def test_syndicate_hub_detection():
    # Build high fan-in hub: 3 senders -> Hub -> 2 receivers
    G = nx.DiGraph()
    for i in range(3):
        G.add_edge(f"SND-{i}", "HUB-1", weight=50000.0)
    for j in range(2):
        G.add_edge("HUB-1", f"RCV-{j}", weight=70000.0)

    res = SyndicateForensics.detect_syndicate_patterns(G)
    assert len(res["hub_bridges"]) >= 1
    hub = res["hub_bridges"][0]
    assert hub["hub_account"] == "HUB-1"
    assert hub["inflow_senders_count"] == 3
    assert hub["outflow_recipients_count"] == 2
