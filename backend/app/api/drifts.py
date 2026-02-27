"""Drift listing and resolution endpoints."""

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user_id

router = APIRouter()


@router.get("/")
async def list_drifts(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """List drifts for user. Placeholder."""
    return []
