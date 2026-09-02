"""
LaundraLens X — Pyvis Graph Visualizer
Generates interactive HTML graph visualizations for the Streamlit dashboard.
Embedded via st.components.v1.html().
"""
from __future__ import annotations

import tempfile
import os
from typing import Optional, Dict

import networkx as nx
from pyvis.network import Network


# Color scheme matching dashboard design
COLORS = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#f59e0b",
    "low": "#6b7280",
    "clean": "#3b82f6",
    "center": "#a78bfa",
    "downstream": "#10b981",
}

BG_COLOR = "#0a0f1e"
FONT_COLOR = "#94a3b8"


def _get_node_color(node_id: str, G: nx.DiGraph, center_id: Optional[str] = None) -> tuple[str, int]:
    """Determine node color and size based on risk attributes."""
    if node_id == center_id:
        return COLORS["center"], 30

    node_data = G.nodes.get(node_id, {})
    suspicious = node_data.get("suspicious", False)
    volume = node_data.get("total_volume", 0.0)

    # Size based on transaction volume (capped)
    size = max(10, min(25, int(volume / 50000)))

    if suspicious:
        return COLORS["critical"], size + 5
    return COLORS["clean"], size


def generate_subgraph_html(
    G: nx.DiGraph,
    center_account_id: str,
    hops: int = 2,
    highlight_accounts: Optional[list] = None,
) -> str:
    """
    Generate Pyvis interactive HTML for a k-hop subgraph.
    Returns HTML string for embedding via st.components.v1.html().
    """
    if center_account_id not in G:
        return _empty_graph_html(f"Account {center_account_id} not in graph")

    # Extract ego subgraph
    ego = nx.ego_graph(G, center_account_id, radius=hops, undirected=False)

    return _build_pyvis_html(
        ego, G,
        center_id=center_account_id,
        highlight_accounts=highlight_accounts or [],
        title=f"Transaction Network — {center_account_id} ({hops}-hop)"
    )


def generate_full_graph_html(G: nx.DiGraph, max_nodes: int = 150) -> str:
    """
    Generate Pyvis HTML for the full graph (sampled if too large).
    """
    if G.number_of_nodes() == 0:
        return _empty_graph_html("No transaction data available")

    # Sample if too large
    if G.number_of_nodes() > max_nodes:
        # Keep suspicious nodes + highest-degree nodes
        suspicious = [n for n in G.nodes() if G.nodes[n].get("suspicious", False)]
        by_degree = sorted(G.nodes(), key=lambda n: G.degree(n), reverse=True)
        keep = set(suspicious) | set(by_degree[:max_nodes - len(suspicious)])
        G_display = G.subgraph(keep).copy()
    else:
        G_display = G

    return _build_pyvis_html(G_display, G, title="LaundraLens X — Transaction Network")


def _build_pyvis_html(
    subgraph: nx.DiGraph,
    full_graph: nx.DiGraph,
    center_id: Optional[str] = None,
    highlight_accounts: Optional[list] = None,
    title: str = "Transaction Network",
) -> str:
    """Internal: build and return the Pyvis HTML."""
    highlight_set = set(highlight_accounts or [])

    net = Network(
        height="450px",
        width="100%",
        bgcolor=BG_COLOR,
        font_color=FONT_COLOR,
        directed=True,
    )
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100},
            "barnesHut": {
                "gravitationalConstant": -3000,
                "springLength": 120,
                "springConstant": 0.04
            }
        },
        "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
            "color": {"inherit": false, "color": "#334155"},
            "smooth": {"type": "curvedCW", "roundness": 0.2},
            "width": 1.5
        },
        "nodes": {
            "shape": "dot",
            "borderWidth": 2,
            "font": {"size": 11, "color": "#94a3b8"}
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100
        }
    }
    """)

    # Add nodes
    for node_id in subgraph.nodes():
        color, size = _get_node_color(node_id, full_graph, center_id)
        node_data = full_graph.nodes.get(node_id, {})
        volume = node_data.get("total_volume", 0.0)
        suspicious = node_data.get("suspicious", False)

        label = node_id if node_id == center_id else node_id[-6:]  # shorten label
        title_str = (
            f"Account: {node_id}<br>"
            f"Volume: Rs {volume:,.0f}<br>"
            f"Suspicious: {'YES' if suspicious else 'No'}<br>"
            f"Community: {node_data.get('community_id', 'N/A')}"
        )

        # Override for highlighted
        if node_id in highlight_set:
            color = COLORS["high"]
            size = 25

        # Glow border for suspicious/center nodes
        border_color = "#ef4444" if suspicious else ("#a78bfa" if node_id == center_id else "#1e3a5f")
        border_width = 3 if (suspicious or node_id == center_id) else 1

        net.add_node(
            node_id,
            label=label,
            color={"background": color, "border": border_color},
            size=size,
            title=title_str,
            borderWidth=border_width,
        )

    # Add edges
    for u, v, data in subgraph.edges(data=True):
        weight = data.get("weight", 0.0)
        tx_count = data.get("tx_count", 1)
        width = max(1, min(6, int(weight / 100000)))

        # Color edges from center or to center
        if u == center_id:
            edge_color = "#ef4444"
        elif v == center_id:
            edge_color = "#10b981"
        else:
            edge_color = "#334155"

        net.add_edge(
            u, v,
            value=width,
            color=edge_color,
            title=f"Rs {weight:,.0f} ({tx_count} txn{'s' if tx_count > 1 else ''})",
        )

    # Save to temp file and read back
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            temp_path = f.name
        net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(temp_path)
        return html
    except Exception as e:
        return _empty_graph_html(f"Graph render error: {e}")


def _empty_graph_html(message: str) -> str:
    """Return placeholder HTML when graph can't be rendered."""
    return f"""
    <div style="
        height:420px;display:flex;align-items:center;justify-content:center;
        background:{BG_COLOR};color:#475569;font-family:Inter,sans-serif;font-size:14px;
        border:1px dashed #1e3a5f;border-radius:12px;
    ">{message}</div>
    """


def generate_syndicate_graph_html(G: nx.DiGraph, syndicates_data: dict) -> str:
    """
    Generate Pyvis HTML specifically highlighting circular round-tripping rings
    and bipartite funnel transit hubs across the network.
    """
    cycles = syndicates_data.get("round_tripping_cycles", [])
    hubs = syndicates_data.get("hub_bridges", [])

    # Collect all relevant nodes
    cycle_nodes = set()
    cycle_edges = set()
    for c in cycles:
        ring = c.get("ring_accounts", [])
        cycle_nodes.update(ring)
        for i in range(len(ring)):
            u = ring[i]
            v = ring[(i + 1) % len(ring)]
            cycle_edges.add((u, v))

    hub_nodes = {h["hub_account"] for h in hubs}
    hub_connected = set()
    for h in hubs:
        hub_connected.update(h.get("connected_accounts", []))

    all_syndicate_nodes = cycle_nodes | hub_nodes | hub_connected
    if not all_syndicate_nodes:
        return _empty_graph_html("No coordinated syndicates detected in current network sample.")

    subgraph = G.subgraph(all_syndicate_nodes).copy()

    net = Network(
        height="480px",
        width="100%",
        bgcolor=BG_COLOR,
        font_color=FONT_COLOR,
        directed=True,
    )
    net.set_options("""
    {
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 120},
            "barnesHut": {
                "gravitationalConstant": -4000,
                "springLength": 140,
                "springConstant": 0.05
            }
        },
        "edges": {
            "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
            "smooth": {"type": "curvedCW", "roundness": 0.25}
        },
        "nodes": {
            "shape": "dot",
            "font": {"size": 11, "color": "#94a3b8"}
        }
    }
    """)

    for node_id in subgraph.nodes():
        if node_id in cycle_nodes:
            color = "#ef4444"
            size = 26
            border = "#f87171"
            title = f"Syndicate Ring Mule: {node_id}<br>Part of Circular Round-Tripping Ring"
        elif node_id in hub_nodes:
            color = "#f59e0b"
            size = 30
            border = "#fbbf24"
            title = f"Bipartite Transit Hub: {node_id}<br>High-Throughput Smurfing Bridge"
        else:
            color = "#3b82f6"
            size = 14
            border = "#1e3a5f"
            title = f"Counterparty Account: {node_id}"

        net.add_node(
            node_id,
            label=node_id[-8:],
            color={"background": color, "border": border},
            size=size,
            title=title,
            borderWidth=3 if (node_id in cycle_nodes or node_id in hub_nodes) else 1,
        )

    for u, v, data in subgraph.edges(data=True):
        weight = data.get("weight", 0.0)
        is_cycle_edge = (u, v) in cycle_edges
        edge_color = "#ef4444" if is_cycle_edge else ("#f59e0b" if (u in hub_nodes or v in hub_nodes) else "#334155")
        width = 3.5 if is_cycle_edge else 1.5

        net.add_edge(
            u, v,
            value=width,
            color=edge_color,
            title=f"Rs {weight:,.0f} ({'CYCLIC FLOW' if is_cycle_edge else 'TRANSFER'})",
        )

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
            temp_path = f.name
        net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            html = f.read()
        os.unlink(temp_path)
        return html
    except Exception as e:
        return _empty_graph_html(f"Syndicate render error: {e}")

