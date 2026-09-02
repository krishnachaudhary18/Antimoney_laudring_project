"""
LaundraLens X — Graph API routes (fully implemented).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.database import get_db
from src.db.models import Transaction

router = APIRouter(prefix="/graph", tags=["graph"])

# Cache the full graph to avoid rebuilding per request
_graph_cache = {}


def _get_or_build_graph(db: Session):
    """Get cached graph or build it."""
    global _graph_cache
    if "graph" not in _graph_cache:
        import pandas as pd
        from src.graph.builder import build_full_graph

        txs = db.query(Transaction).all()
        df = pd.DataFrame([{
            "transaction_id": t.transaction_id, "timestamp": t.timestamp,
            "sender_account_id": t.sender_account_id, "receiver_account_id": t.receiver_account_id,
            "amount": float(t.amount), "ground_truth_pattern": t.ground_truth_pattern,
        } for t in txs])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        alert_ts = datetime(2026, 8, 14, 11, 30, 0)
        _graph_cache["graph"] = build_full_graph(df, alert_timestamp=alert_ts)

    return _graph_cache["graph"]


@router.get("/syndicates/detect")
def detect_syndicates(db: Session = Depends(get_db)):
    """Detect circular round-tripping and funneling mule syndicates across the entire transaction network."""
    from src.graph.syndicate import SyndicateForensics
    G = _get_or_build_graph(db)
    syndicates = SyndicateForensics.detect_syndicate_patterns(G)
    return syndicates


@router.get("/{account_id}")
def get_account_graph(
    account_id: str,
    hops: int = Query(default=2, ge=1, le=3),
    db: Session = Depends(get_db),
):
    """Get Pyvis HTML subgraph for an account."""
    from src.graph.visualizer import generate_subgraph_html

    G = _get_or_build_graph(db)
    html = generate_subgraph_html(G, account_id, hops=hops)
    return {"account_id": account_id, "hops": hops, "html": html}


@router.get("/{account_id}/neighbors")
def get_neighbors(
    account_id: str,
    direction: str = Query(default="both", pattern="^(in|out|both)$"),
    db: Session = Depends(get_db),
):
    """Get immediate graph neighbors."""
    from src.graph.traversal import get_neighbors
    G = _get_or_build_graph(db)
    return get_neighbors(G, account_id, direction=direction)


@router.get("/{account_id}/expand")
def expand_account(
    account_id: str,
    hops: int = Query(default=2, ge=1, le=4),
    db: Session = Depends(get_db),
):
    """Get k-hop expansion data (nodes + edges)."""
    from src.graph.traversal import expand_k_hop
    G = _get_or_build_graph(db)
    return expand_k_hop(G, account_id, hops=hops)


@router.get("/paths/{source}/{target}")
def find_paths(
    source: str,
    target: str,
    max_depth: int = Query(default=4, ge=1, le=6),
    db: Session = Depends(get_db),
):
    """Find transaction paths between two accounts."""
    from src.graph.traversal import find_paths
    G = _get_or_build_graph(db)
    return find_paths(G, source, target, max_depth)


@router.delete("/cache")
def clear_graph_cache():
    """Clear the graph cache (admin endpoint)."""
    global _graph_cache
    _graph_cache.clear()
    return {"message": "Graph cache cleared"}


