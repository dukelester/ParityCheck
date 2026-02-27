"""Environment CRUD endpoints."""

from fastapi import APIRouter, Depends

from app.api.auth import get_current_user_id

router = APIRouter()


@router.get("/")
async def list_environments(user_id: str = Depends(get_current_user_id)) -> list[dict]:
    """List user's environments. Placeholder."""
    return [{"id": "1", "name": "dev", "type": "dev"}, {"id": "2", "name": "prod", "type": "prod"}]
