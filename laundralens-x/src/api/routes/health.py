"""Health check route."""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "LaundraLens X",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
