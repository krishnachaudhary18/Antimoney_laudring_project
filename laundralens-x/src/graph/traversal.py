"""
LaundraLens X — Graph Traversal
k-hop expansion, path finding, and connected entity discovery.
"""
from __future__ import annotations

from typing import List, Dict, Optional
import networkx as nx


def get_neighbors(G: nx.DiGraph, account_id: str, direction: str = "both") -> Dict:
    """Get immediate neighbors of an account."""
    if account_id not in G:
        return {"account_id": account_id, "neighbors": [], "count": 0}

    if direction == "in":
        neighbors = list(G.predecessors(account_id))
    elif direction == "out":
        neighbors = list(G.successors(account_id))
    else:
        neighbors = list(set(G.predecessors(account_id)) | set(G.successors(account_id)))

    return {
        "account_id": account_id,
        "direction": direction,
        "neighbors": neighbors,
        "count": len(neighbors),
    }


def expand_k_hop(G: nx.DiGraph, account_id: str, hops: int = 2) -> Dict:
    """
    Expand k hops from an account.
    Returns nodes and edges in the subgraph.
    """
    if account_id not in G:
        return {"account_id": account_id, "hops": hops, "nodes": [], "edges": []}

    ego = nx.ego_graph(G, account_id, radius=hops, undirected=False)

    nodes = []
    for node in ego.nodes():
        node_data = G.nodes[node]
        nodes.append({
            "account_id": node,
            "suspicious": node_data.get("suspicious", False),
            "community_id": node_data.get("community_id"),
            "total_volume": node_data.get("total_volume", 0.0),
            "is_center": node == account_id,
        })

    edges = []
    for u, v, data in ego.edges(data=True):
        edges.append({
            "from": u,
            "to": v,
            "weight": round(data.get("weight", 0.0), 2),
            "tx_count": data.get("tx_count", 1),
        })

    return {
        "account_id": account_id,
        "hops": hops,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def find_paths(
    G: nx.DiGraph,
    source: str,
    target: str,
    max_depth: int = 4,
) -> Dict:
    """Find all simple paths between source and target up to max_depth."""
    if source not in G or target not in G:
        return {"source": source, "target": target, "paths": [], "path_count": 0}

    try:
        paths = list(nx.all_simple_paths(G, source, target, cutoff=max_depth))
    except (nx.NetworkXError, nx.exception.NodeNotFound):
        paths = []

    # Annotate paths with edge data
    path_details = []
    for path in paths[:10]:  # limit to 10 paths
        edges = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            if G.has_edge(u, v):
                edges.append({
                    "from": u,
                    "to": v,
                    "amount": round(G[u][v].get("weight", 0.0), 2),
                })
        path_details.append({"nodes": path, "edges": edges, "hops": len(path) - 1})

    return {
        "source_account": source,
        "target_account": target,
        "paths": path_details,
        "path_count": len(paths),
        "hops": max_depth,
    }


def get_connected_entities(G: nx.DiGraph, account_id: str) -> Dict:
    """Get all accounts in the same weakly connected component."""
    if account_id not in G:
        return {"account_id": account_id, "connected_accounts": [], "count": 0}

    # Weakly connected component
    G_undirected = G.to_undirected()
    component = nx.node_connected_component(G_undirected, account_id)
    connected = [a for a in component if a != account_id]

    return {
        "account_id": account_id,
        "connected_accounts": connected[:50],  # cap for display
        "count": len(connected),
    }
