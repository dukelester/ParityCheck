"""Workspace CRUD and management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import User, Workspace, WorkspaceMember
from app.db.session import get_db
from app.services.workspace import get_or_create_default_workspace, require_workspace_role

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


@router.get("/{workspace_id}/members")
async def list_members(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List members for a workspace (requires member access)."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "member")
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")

    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == ws.id)
        .order_by(WorkspaceMember.created_at)
    )
    rows = result.all()
    return [
        {
            "id": str(member.id),
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": member.role,
            "joined_at": member.created_at.isoformat(),
        }
        for member, user in rows
    ]


@router.post("/{workspace_id}/members")
async def invite_member(
    workspace_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add a member to workspace by email. Requires admin or owner."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "admin")
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized to manage members")

    email = (payload.get("email") or "").strip().lower()
    role = (payload.get("role") or "member").strip()
    if role not in {"member", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User with that email was not found")

    # Check existing membership
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == ws.id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")

    member = WorkspaceMember(workspace_id=ws.id, user_id=user.id, role=role)
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return {
        "id": str(member.id),
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": member.role,
        "joined_at": member.created_at.isoformat(),
    }


@router.patch("/{workspace_id}/members/{member_id}")
async def update_member_role(
    workspace_id: str,
    member_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a member's role (admin or member). Owner role cannot be changed here."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "owner")
    if not ws:
        raise HTTPException(status_code=403, detail="Only workspace owners can change roles")

    new_role = (payload.get("role") or "").strip()
    if new_role not in {"member", "admin"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(
        select(WorkspaceMember, User)
        .join(User, WorkspaceMember.user_id == User.id)
        .where(
            WorkspaceMember.id == UUID(member_id),
            WorkspaceMember.workspace_id == ws.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Member not found")
    member, user = row

    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Owner role cannot be changed")

    member.role = new_role
    await db.commit()
    await db.refresh(member)

    return {
        "id": str(member.id),
        "user_id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": member.role,
        "joined_at": member.created_at.isoformat(),
    }


@router.delete("/{workspace_id}/members/{member_id}")
async def remove_member(
    workspace_id: str,
    member_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove a member from workspace. Owners cannot be removed via this endpoint."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "admin")
    if not ws:
        raise HTTPException(status_code=403, detail="Not authorized to manage members")

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.id == UUID(member_id),
            WorkspaceMember.workspace_id == ws.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Owner cannot be removed")

    await db.delete(member)
    await db.commit()
    return {"message": "Member removed"}
