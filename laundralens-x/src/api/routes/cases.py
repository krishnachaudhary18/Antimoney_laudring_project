"""Cases API routes — stub, fully implemented in Phase 7."""
from fastapi import APIRouter

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/{case_id}")
def get_case(case_id: str):
    return {"case_id": case_id, "status": "case module not yet initialized"}


@router.post("/{case_id}/report")
def generate_report(case_id: str):
    return {"case_id": case_id, "status": "report module not yet initialized"}
