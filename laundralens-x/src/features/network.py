"""
LaundraLens X — Network Feature Engine
Computes graph-based features for accounts using the transaction graph.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import networkx as nx

EPSILON = 1e-6


def build_transaction_graph(
    transactions_df: pd.DataFrame,
    alert_timestamp: Optional[datetime] = None,
    lookback_days: int = 30,
) -> nx.DiGraph:
    """
    Build a directed weighted NetworkX graph from transactions.
    Nodes = accounts, Edges = transactions (weight = amount).
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    if alert_timestamp:
        cutoff = alert_timestamp
        start = alert_timestamp - timedelta(days=lookback_days)
        df = df[(df["timestamp"] >= start) & (df["timestamp"] <= cutoff)]

    G = nx.DiGraph()

    for _, row in df.iterrows():
        sender = row["sender_account_id"]
        receiver = row["receiver_account_id"]
        amount = float(row["amount"])
        ts = row["timestamp"]

        # Add nodes
        if not G.has_node(sender):
            G.add_node(sender)
        if not G.has_node(receiver):
            G.add_node(receiver)

        # Add or update edge
        if G.has_edge(sender, receiver):
            G[sender][receiver]["weight"] += amount
            G[sender][receiver]["tx_count"] += 1
            G[sender][receiver]["transactions"].append({
                "transaction_id": row.get("transaction_id", ""),
                "amount": amount,
                "timestamp": str(ts),
            })
        else:
            G.add_edge(sender, receiver, weight=amount, tx_count=1, transactions=[{
                "transaction_id": row.get("transaction_id", ""),
                "amount": amount,
                "timestamp": str(ts),
            }])

    return G


def compute_network_features(
    account_id: str,
    G: nx.DiGraph,
    suspicious_account_ids: Optional[list] = None,
) -> dict:
    """
    Compute network/graph features for a specific account.

    Args:
        account_id: Target account node
        G: Full transaction graph
        suspicious_account_ids: Known suspicious nodes (for neighbor analysis)

    Returns:
        dict with network features and graph_signal [0,1]
    """
    if account_id not in G:
        return {
            "account_id": account_id,
            "in_graph": False,
            "graph_signal": 0.0,
        }

    # Degree metrics
    in_degree = G.in_degree(account_id)
    out_degree = G.out_degree(account_id)
    weighted_in = float(G.in_degree(account_id, weight="weight"))
    weighted_out = float(G.out_degree(account_id, weight="weight"))
    total_degree = in_degree + out_degree

    # Fan-in / Fan-out
    fan_in = in_degree    # number of unique senders
    fan_out = out_degree  # number of unique receivers

    # Unique counterparties
    neighbors_in = set(G.predecessors(account_id))
    neighbors_out = set(G.successors(account_id))
    counterparty_count = len(neighbors_in | neighbors_out)

    # Centrality (approximate for speed — avoid expensive betweenness on large graphs)
    # Use degree centrality as fast approximation
    n_nodes = G.number_of_nodes()
    degree_centrality = total_degree / max(n_nodes - 1, 1)

    # Betweenness centrality on ego subgraph (2-hop) — much faster than full graph
    ego = nx.ego_graph(G, account_id, radius=2, undirected=False)
    if ego.number_of_nodes() > 1:
        try:
            bc = nx.betweenness_centrality(ego, normalized=True)
            betweenness = bc.get(account_id, 0.0)
        except Exception:
            betweenness = 0.0
    else:
        betweenness = 0.0

    # Community detection using simple connected components (Louvain handled in builder)
    community_id = None  # set by graph builder

    # Suspicious neighbors
    suspicious_neighbor_count = 0
    if suspicious_account_ids:
        suspicious_set = set(suspicious_account_ids)
        suspicious_neighbor_count = len((neighbors_in | neighbors_out) & suspicious_set)

    # k-hop network size (2-hop)
    try:
        two_hop = set()
        for n in neighbors_in | neighbors_out:
            two_hop.update(G.predecessors(n))
            two_hop.update(G.successors(n))
        two_hop.discard(account_id)
        k_hop_network_size = len(two_hop)
    except Exception:
        k_hop_network_size = 0

    # Network depth (max path length from account)
    try:
        lengths = nx.single_source_shortest_path_length(G, account_id, cutoff=4)
        network_depth = max(lengths.values()) if lengths else 0
    except Exception:
        network_depth = 0

    # --- Graph Signal [0,1] ---
    # High fan-out + high betweenness + high weighted-out = suspicious hub
    fan_out_signal = min(fan_out / 10.0, 1.0)
    fan_in_signal = min(fan_in / 10.0, 1.0)
    centrality_signal = min(betweenness * 5.0, 1.0)  # amplify for small ego graphs
    imbalance = abs(weighted_out - weighted_in) / (max(weighted_in, weighted_out) + EPSILON)
    imbalance_signal = float(np.clip(imbalance, 0.0, 1.0))

    graph_signal = float(np.clip(
        0.30 * fan_out_signal +
        0.20 * fan_in_signal +
        0.25 * centrality_signal +
        0.25 * imbalance_signal,
        0.0, 1.0
    ))

    return {
        "account_id": account_id,
        "in_graph": True,
        # Degree
        "in_degree": in_degree,
        "out_degree": out_degree,
        "weighted_in_degree": round(weighted_in, 2),
        "weighted_out_degree": round(weighted_out, 2),
        "total_degree": total_degree,
        "fan_in": fan_in,
        "fan_out": fan_out,
        "counterparty_count": counterparty_count,
        # Centrality
        "degree_centrality": round(degree_centrality, 4),
        "betweenness_centrality": round(betweenness, 4),
        # Network scope
        "k_hop_network_size": k_hop_network_size,
        "network_depth": network_depth,
        "suspicious_neighbor_count": suspicious_neighbor_count,
        "community_id": community_id,
        # Composite
        "graph_signal": round(graph_signal, 4),
    }
