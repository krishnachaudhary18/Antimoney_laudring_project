"""
LaundraLens X — Graph Builder
Constructs the full NetworkX transaction graph with community detection.
"""
from __future__ import annotations

import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

import networkx as nx
import pandas as pd

try:
    import community as community_louvain
    LOUVAIN_AVAILABLE = True
except ImportError:
    LOUVAIN_AVAILABLE = False


def build_full_graph(
    transactions_df: pd.DataFrame,
    alert_timestamp: Optional[datetime] = None,
    lookback_days: int = 30,
    detect_communities: bool = True,
) -> nx.DiGraph:
    """
    Build complete directed transaction graph.

    Nodes = accounts (with attributes)
    Edges = transactions (weight = total amount, tx_count = number of txns)
    Communities detected via Louvain (undirected projection).
    """
    df = transactions_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    if alert_timestamp:
        start = alert_timestamp - timedelta(days=lookback_days)
        df = df[(df["timestamp"] >= start) & (df["timestamp"] <= alert_timestamp)]

    G = nx.DiGraph()

    # Build graph
    for _, row in df.iterrows():
        sender = row["sender_account_id"]
        receiver = row["receiver_account_id"]
        amount = float(row["amount"])
        ts = str(row["timestamp"])
        scenario = row.get("scenario_id")
        ground_truth = row.get("ground_truth_pattern")
        tx_id = row.get("transaction_id", "")

        for node_id in [sender, receiver]:
            if not G.has_node(node_id):
                G.add_node(node_id, suspicious=False, community_id=None, total_volume=0.0)

        if G.has_edge(sender, receiver):
            G[sender][receiver]["weight"] += amount
            G[sender][receiver]["tx_count"] += 1
            G[sender][receiver]["transactions"].append({
                "transaction_id": tx_id, "amount": amount, "timestamp": ts
            })
        else:
            G.add_edge(sender, receiver,
                weight=amount, tx_count=1,
                transactions=[{"transaction_id": tx_id, "amount": amount, "timestamp": ts}],
                scenario_id=scenario,
            )

        # Update node volume
        G.nodes[sender]["total_volume"] = G.nodes[sender].get("total_volume", 0.0) + amount
        G.nodes[receiver]["total_volume"] = G.nodes[receiver].get("total_volume", 0.0) + amount

        # Mark suspicious nodes
        if ground_truth == "synthetic_suspicious_pattern":
            G.nodes[sender]["suspicious"] = True
            G.nodes[receiver]["suspicious"] = True

    # Community detection via Louvain (on undirected version)
    if detect_communities and LOUVAIN_AVAILABLE and G.number_of_nodes() > 1:
        try:
            G_undirected = G.to_undirected()
            partition = community_louvain.best_partition(G_undirected, random_state=42)
            for node, community_id in partition.items():
                if G.has_node(node):
                    G.nodes[node]["community_id"] = community_id
        except Exception:
            pass  # Community detection is best-effort

    return G


def get_subgraph(G: nx.DiGraph, account_id: str, hops: int = 2) -> nx.DiGraph:
    """Extract k-hop ego subgraph around an account."""
    if account_id not in G:
        return nx.DiGraph()
    ego = nx.ego_graph(G, account_id, radius=hops, undirected=False)
    return ego


def save_graph(G: nx.DiGraph, path: Path):
    """Pickle the graph for fast reload."""
    with open(path, "wb") as f:
        pickle.dump(G, f)


def load_graph(path: Path) -> Optional[nx.DiGraph]:
    """Load pickled graph."""
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return pickle.load(f)
