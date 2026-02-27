"""Environment CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import Environment, Report
from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def list_environments(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List user's environments with last report timestamp."""
    user_uuid = UUID(user_id)
    subq = (
        select(Report.env_id, func.max(Report.timestamp).label("last_ts"))
        .group_by(Report.env_id)
    ).subquery()
    result = await db.execute(
        select(Environment, subq.c.last_ts)
        .outerjoin(subq, Environment.id == subq.c.env_id)
        .where(Environment.user_id == user_uuid)
        .order_by(Environment.name)
    )
    rows = result.all()
    return [
        {
            "id": str(env.id),
            "name": env.name,
            "type": env.type,
            "last_report": env_ts.isoformat() if env_ts else None,
        }
        for env, env_ts in rows
    ]
