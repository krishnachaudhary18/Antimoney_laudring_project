"""
Unit tests for Graph Intelligence and Lineage Tracing.
"""
from datetime import datetime, timedelta
import pandas as pd
from src.graph.builder import build_full_graph
from src.graph.traversal import expand_k_hop, find_paths
from src.graph.lineage import trace_potential_lineage
from src.graph.visualizer import generate_subgraph_html


def test_graph_and_traversal():
    base = datetime(2026, 8, 14, 10, 0, 0)
    data = [
        {"transaction_id": "TX1", "timestamp": base, "sender_account_id": "ACC-A", "receiver_account_id": "ACC-B", "amount": 100000.0},
        {"transaction_id": "TX2", "timestamp": base + timedelta(minutes=10), "sender_account_id": "ACC-B", "receiver_account_id": "ACC-C", "amount": 50000.0},
        {"transaction_id": "TX3", "timestamp": base + timedelta(minutes=20), "sender_account_id": "ACC-C", "receiver_account_id": "ACC-D", "amount": 40000.0},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    G = build_full_graph(df)
    assert G.number_of_nodes() == 4

    ego = expand_k_hop(G, "ACC-B", hops=1)
    assert ego["node_count"] >= 2

    paths = find_paths(G, "ACC-A", "ACC-D", max_depth=3)
    assert paths["path_count"] == 1
    assert paths["paths"][0]["nodes"] == ["ACC-A", "ACC-B", "ACC-C", "ACC-D"]


def test_lineage_tracing():
    base = datetime(2026, 8, 14, 10, 0, 0)
    data = [
        {"transaction_id": "ORIGIN", "timestamp": base, "sender_account_id": "ACC-A", "receiver_account_id": "ACC-B", "amount": 100000.0},
        {"transaction_id": "DOWN-1", "timestamp": base + timedelta(minutes=30), "sender_account_id": "ACC-B", "receiver_account_id": "ACC-C", "amount": 80000.0},
    ]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    res = trace_potential_lineage("ORIGIN", df, max_depth=2)
    assert res["lineage_type"] == "potential_downstream_lineage"
    assert len(res["candidate_downstream_transactions"]) == 1
    assert res["lineage_strength"] > 0.0


def test_pyvis_rendering():
    base = datetime(2026, 8, 14, 10, 0, 0)
    data = [{"transaction_id": "TX1", "timestamp": base, "sender_account_id": "ACC-A", "receiver_account_id": "ACC-B", "amount": 100000.0}]
    df = pd.DataFrame(data)
    G = build_full_graph(df)
    html = generate_subgraph_html(G, "ACC-B", hops=1)
    assert "<html" in html or "id=" in html or "vis" in html
