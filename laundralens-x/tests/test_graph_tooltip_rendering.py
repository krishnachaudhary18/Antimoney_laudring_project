"""
Regression test for Graph Node Tooltip and Detail Rendering.
Verifies Requirement 9:
1. Node and edge titles/tooltips are clean plain text and do NOT contain raw HTML markup (<div, <b, <span, <br>).
2. Selected node account ID is a valid account ID (e.g. 'ACC-B-001'), never a raw HTML string.
3. Node detail payloads and hover tooltips contain valid account identifiers and structured lines without HTML tag leakage.
"""
import re
import pytest
from src.db.database import SessionLocal
from src.api.routes.graph import _get_or_build_graph
from src.graph.visualizer import generate_subgraph_html, generate_syndicate_graph_html
from src.graph.syndicate import SyndicateForensics


def test_subgraph_tooltips_contain_no_raw_html():
    """Verify that node and edge titles in the generated HTML do not contain raw HTML tags."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    html = generate_subgraph_html(G, "ACC-B-001", hops=1, mode="investigation")
    assert isinstance(html, str)
    assert len(html) > 500

    # Extract all node title definitions from the Vis.js data definition
    # PyVis writes nodes as JSON array or JS objects
    # Check that tooltip strings do not contain raw HTML markup tags
    raw_html_patterns = [
        r"<div\b",
        r"</div>",
        r"<b\b",
        r"</b>",
        r"<span\b",
        r"</span>",
        r"<br\s*/?>",
    ]

    # Find the nodes array definition in the HTML
    nodes_match = re.search(r'nodes\s*=\s*new\s+vis\.DataSet\((\[.*?\])\);', html, re.DOTALL)
    assert nodes_match is not None, "Vis.js nodes DataSet not found in HTML"

    nodes_json_str = nodes_match.group(1)
    import json
    nodes = json.loads(nodes_json_str)

    assert len(nodes) >= 6, "Expected at least 6 nodes in Level 1 investigation view"

    for node in nodes:
        node_id = node.get("id")
        title = node.get("title", "")
        # Verify node ID is a clean account ID
        assert node_id.startswith("ACC-") or node_id.startswith("SUMMARY-"), f"Unexpected node_id: {node_id}"
        assert not any(tag in node_id for tag in ["<div", "<span", "<b"]), "node_id contains HTML tags!"

        # Verify title does not contain raw HTML markup
        for pattern in raw_html_patterns:
            assert not re.search(pattern, title, re.IGNORECASE), (
                f"Node {node_id} title contains raw HTML matching '{pattern}': {title}"
            )

    # Find the edges array definition in the HTML
    edges_match = re.search(r'edges\s*=\s*new\s+vis\.DataSet\((\[.*?\])\);', html, re.DOTALL)
    assert edges_match is not None, "Vis.js edges DataSet not found in HTML"

    edges = json.loads(edges_match.group(1))
    assert len(edges) >= 5, "Expected at least 5 edges in Level 1 investigation view"

    for edge in edges:
        edge_title = edge.get("title", "")
        for pattern in raw_html_patterns:
            assert not re.search(pattern, edge_title, re.IGNORECASE), (
                f"Edge title contains raw HTML matching '{pattern}': {edge_title}"
            )


def test_syndicate_graph_tooltips_contain_no_raw_html():
    """Verify that syndicate node and edge titles do not contain <br> or other HTML tags."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    syndicates = SyndicateForensics.detect_syndicate_patterns(G)
    html = generate_syndicate_graph_html(G, syndicates)

    nodes_match = re.search(r'nodes\s*=\s*new\s+vis\.DataSet\((\[.*?\])\);', html, re.DOTALL)
    if nodes_match:
        import json
        nodes = json.loads(nodes_match.group(1))
        for node in nodes:
            title = node.get("title", "")
            assert "<br>" not in title, f"Syndicate node title contains <br>: {title}"
            assert "<div" not in title, f"Syndicate node title contains <div: {title}"


def test_selected_account_callback_extracts_clean_id():
    """Verify that the client-side data store keys are exact account IDs and not HTML strings."""
    with SessionLocal() as db:
        G = _get_or_build_graph(db)

    html = generate_subgraph_html(G, "ACC-B-001", hops=1, mode="investigation")

    # Extract graphNodesData from injected script
    data_match = re.search(r'const graphNodesData\s*=\s*(\{.*?\});\s*const centerAccountId', html, re.DOTALL)
    assert data_match is not None, "graphNodesData not found in HTML"

    import json
    client_data = json.loads(data_match.group(1))

    # ACC-B-001 should be present as a key
    assert "ACC-B-001" in client_data
    acc_info = client_data["ACC-B-001"]
    assert acc_info["account_id"] == "ACC-B-001"
    assert not acc_info["account_id"].startswith("<")
    assert acc_info["role"] == "Target Subject Account"

    # All keys must be valid account IDs
    for key, val in client_data.items():
        assert key.startswith("ACC-") or key.startswith("SUMMARY-")
        assert not key.startswith("<div")
        assert val["account_id"] == key
