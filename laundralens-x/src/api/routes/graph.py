"""Graph API routes — stub, fully implemented in Phase 4."""
from fastapi import APIRouter

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{account_id}")
def get_graph(account_id: str, hops: int = 2):
    return {"account_id": account_id, "hops": hops, "status": "graph module not yet initialized"}


@router.get("/{account_id}/expand")
def expand_graph(account_id: str, hops: int = 2):
    return {"account_id": account_id, "hops": hops, "status": "graph module not yet initialized"}


@router.get("/{account_id}/lineage")
def get_lineage(account_id: str):
    return {"account_id": account_id, "status": "lineage module not yet initialized"}
