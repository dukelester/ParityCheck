"""Workspace CRUD and management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import Workspace, WorkspaceMember
from app.db.session import get_db
from app.services.workspace import get_or_create_default_workspace

router = APIRouter()


@router.get("/")
async def list_workspaces(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List workspaces the user belongs to."""
    user_uuid = UUID(user_id)
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_uuid)
        .order_by(Workspace.name)
    )
    workspaces = result.scalars().all()
    return [
        {
            "id": str(ws.id),
            "name": ws.name,
            "plan": ws.plan,
            "role": "owner" if ws.owner_id == user_uuid else "member",
        }
        for ws in workspaces
    ]


@router.get("/default")
async def get_default_workspace(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get or create default workspace."""
    ws = await get_or_create_default_workspace(db, UUID(user_id))
    await db.commit()
    return {
        "id": str(ws.id),
        "name": ws.name,
        "plan": ws.plan,
    }


@router.get("/{workspace_id}/usage")
async def get_workspace_usage(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get plan usage for workspace."""
    from sqlalchemy import func

    from app.db.models import Alert, Environment
    from app.services.workspace import (
        PLAN_LIMITS,
        get_workspace_for_user,
    )

    ws = await get_workspace_for_user(db, UUID(workspace_id), UUID(user_id))
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    limits = PLAN_LIMITS.get(ws.plan, PLAN_LIMITS["free"])
    env_count = await db.scalar(
        select(func.count()).select_from(Environment).where(
            Environment.workspace_id == ws.id
        )
    )
    alert_count = await db.scalar(
        select(func.count()).select_from(Alert).where(
            Alert.workspace_id == ws.id
        )
    )
    return {
        "plan": ws.plan,
        "environments": {"used": env_count or 0, "limit": limits["environments"]},
        "slack_alerts": {"used": alert_count or 0, "allowed": limits["slack_alerts"]},
        "history_days": limits["history_days"],
    }
