"""Report upload and retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import get_current_user_id
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


@router.post("/", response_model=ReportResponse)
async def create_report(
    payload: ReportCreate,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Receive report from CLI. Store in DB and compute drift."""
    # TODO: Resolve env name to env_id, persist to DB, trigger drift analysis
    return {
        "id": "placeholder-report-id",
        "env": payload.env,
        "timestamp": "2025-02-27T00:00:00Z",
        "status": "stored",
    }


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get report by ID."""
    raise HTTPException(status_code=404, detail="Not implemented")
