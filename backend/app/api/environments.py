"""Environment CRUD endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.core.utils import iso_utc
from app.db.models import Environment, Report, WorkspaceMember
from app.db.session import get_db
from app.services.workspace import set_baseline as do_set_baseline

router = APIRouter()


@router.get("/")
async def list_environments(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
) -> list[dict]:
    """List user's environments with last report timestamp."""
    user_uuid = UUID(user_id)
    subq = (
        select(Report.env_id, func.max(Report.timestamp).label("last_ts"))
        .group_by(Report.env_id)
    ).subquery()
    q = (
        select(Environment, subq.c.last_ts)
        .outerjoin(subq, Environment.id == subq.c.env_id)
        .where(
            or_(
                Environment.user_id == user_uuid,
                Environment.workspace_id.in_(
                    select(WorkspaceMember.workspace_id).where(
                        WorkspaceMember.user_id == user_uuid
                    )
                ),
            )
        )
        .order_by(Environment.name)
    )
    if workspace_id:
        q = q.where(Environment.workspace_id == UUID(workspace_id))
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "id": str(env.id),
            "name": env.name,
            "type": env.type,
            "workspace_id": str(env.workspace_id) if env.workspace_id else None,
            "is_baseline": env.is_baseline,
            "last_report": iso_utc(env_ts) if env_ts else None,
        }
        for env, env_ts in rows
    ]


@router.post("/{env_id}/set-baseline")
async def set_baseline(
    env_id: str,
    workspace_id: str = Query(..., description="Workspace ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Set environment as baseline for workspace."""
    ok = await do_set_baseline(
        db, UUID(workspace_id), UUID(env_id), UUID(user_id)
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Environment or workspace not found")
    return {"message": "Baseline set"}
