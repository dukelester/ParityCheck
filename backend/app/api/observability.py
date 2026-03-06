"""System observability endpoints for in-app status."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.services.auth import decode_token, get_user_by_id
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
bearer = HTTPBearer(auto_error=False)


@router.get("/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    """Return basic system health for display in the dashboard/settings UI."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    decoded = decode_token(credentials.credentials)
    if not decoded or decoded.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = decoded.get("sub")
    user = await get_user_by_id(db, UUID(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Database check
    db_ok = True
    db_error: str | None = None
    try:
        await db.execute(select(1))
    except Exception as e:  # pragma: no cover - defensive
        db_ok = False
        db_error = str(e)

    # Redis check
    redis_ok = True
    redis_error: str | None = None
    try:
        client = redis_from_url(settings.REDIS_URL)
        pong = await client.ping()
        if not pong:
            redis_ok = False
    except Exception as e:  # pragma: no cover - defensive
        redis_ok = False
        redis_error = str(e)

    overall = "ok" if db_ok and redis_ok else "degraded"

    return {
        "status": overall,
        "components": {
            "database": {"status": "ok" if db_ok else "error", "error": db_error},
            "redis": {"status": "ok" if redis_ok else "error", "error": redis_error},
        },
        "rate_limits": {
            "plan": user.role or "user",
            "enforced": False,
            "note": "Per-user API rate limits are not currently enforced.",
        },
    }

