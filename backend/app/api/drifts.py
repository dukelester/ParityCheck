"""Drift listing and resolution endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.core.utils import iso_utc
from app.db.models import Drift, Environment, Report, WorkspaceMember
from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def list_drifts(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
    env: str | None = Query(None, description="Filter by environment name"),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200),
) -> list[dict]:
    """List drifts for user's environments."""
    user_uuid = UUID(user_id)
    q = (
        select(Drift, Report, Environment)
        .join(Report, Drift.report_id == Report.id)
        .join(Environment, Report.env_id == Environment.id)
        .where(
            or_(
                Environment.user_id == user_uuid,
                Environment.workspace_id.in_(
                    select(WorkspaceMember.workspace_id).where(
                        WorkspaceMember.user_id == user_uuid
                    )
                ),
            ),
            Drift.resolved == False,
        )
        .order_by(Drift.created_at.desc())
        .limit(limit)
    )
    if workspace_id:
        q = q.where(Environment.workspace_id == UUID(workspace_id))
    if env:
        q = q.where(Environment.name == env)
    if severity:
        q = q.where(Drift.severity == severity)
    result = await db.execute(q)
    rows = result.all()
    return [
        {
            "id": str(d.id),
            "report_id": str(d.report_id),
            "env": e.name,
            "type": d.type,
            "severity": d.severity,
            "key": d.key,
            "value_a": d.value_a,
            "value_b": d.value_b,
            "details": d.details or {},
            "created_at": iso_utc(d.created_at),
        }
        for d, r, e in rows
    ]
