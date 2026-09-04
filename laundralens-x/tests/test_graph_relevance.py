"""
Unit tests for Graph Relevance & Filtering Layer in LaundraLens X.
Verifies:
1. Investigation mode prioritizes target, inflow source, and outflow recipients.
2. Progressive depth expansion (Level 1, 2, 3) filters background noise.
3. Summary nodes aggregate excess counterparties.
4. Full network mode remains available when explicitly requested.
"""
import pytest
import networkx as nx
from datetime import datetime, timedelta
import pandas as pd

from src.db.database import SessionLocal
from src.api.routes.graph import _get_or_build_graph
from src.graph.relevance import rank_and_filter_investigation_network
from src.graph.visualizer import generate_subgraph_html


def test_investigation_mode_filters_irrelevant_nodes():
    """Level 1 investigation view should isolate target, inflow, and outflows without 100s of background nodes."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    # ACC-B-001 has 100+ nodes in undirected 2-hop radius, but Level 1 investigation view should be exactly 6 nodes
    sub, meta = rank_and_filter_investigation_network(G, "ACC-B-001", depth=1, mode="investigation")

    assert sub.number_of_nodes() == 6
    assert sub.number_of_edges() == 5
    assert "ACC-B-001" in sub
    assert sub.nodes["ACC-B-001"]["role"] == "target"

    # Inflow source
    assert "ACC-A-001" in sub
    assert sub.nodes["ACC-A-001"]["role"] == "inflow_source"

    # Outflow recipients
    for mule in ["ACC-C-001", "ACC-D-001", "ACC-E-001", "ACC-F-001"]:
        assert mule in sub
        assert sub.nodes[mule]["role"] == "outflow_recipient"
        assert sub.has_edge("ACC-B-001", mule)


def test_investigation_level_2_progressive_expansion():
    """Level 2 investigation view should include candidate downstream transfers and summarize remaining noise."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    sub, meta = rank_and_filter_investigation_network(G, "ACC-B-001", depth=2, mode="investigation")

    # Rather than 100 chaotic nodes, level 2 keeps it concise (around 20-25 nodes)
    assert 10 <= sub.number_of_nodes() <= 30
    assert meta["depth"] == 2

    # Check for presence of summary nodes or downstream nodes
    roles = [d.get("role") for _, d in sub.nodes(data=True)]
    assert "downstream" in roles or "summary" in roles


def test_full_network_mode_available():
    """Full network mode should return the broader ego-network when explicitly requested."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    sub_full, meta_full = rank_and_filter_investigation_network(G, "ACC-B-001", depth=2, mode="full")

    # Full mode returns the full 100 nodes
    assert sub_full.number_of_nodes() >= 50
    assert meta_full["mode"] == "full"


def test_visualizer_html_contains_investigation_ui():
    """HTML output should include legend, role styling, and client drawer."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    html = generate_subgraph_html(G, "ACC-B-001", hops=1, mode="investigation")
    assert "graph-legend-bar" in html
    assert "graph-details-drawer" in html
    assert "ACC-B-001" in html
    assert "ACC-A-001" in html
    assert "INFLOW" in html or "Primary Inflow" in html
