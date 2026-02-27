"""Ignore rules CRUD."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import IgnoreRule
from app.db.session import get_db
from app.services.workspace import require_workspace_role

router = APIRouter()


class IgnoreRuleCreate(BaseModel):
    workspace_id: str
    type: str  # env_var, dependency, runtime
    key_pattern: str


class IgnoreRuleResponse(BaseModel):
    id: str
    workspace_id: str
    type: str
    key_pattern: str


@router.get("/")
async def list_ignore_rules(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List ignore rules for workspace."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "admin")
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = await db.execute(
        select(IgnoreRule).where(IgnoreRule.workspace_id == UUID(workspace_id))
    )
    rules = result.scalars().all()
    return [
        {"id": str(r.id), "workspace_id": str(r.workspace_id), "type": r.type, "key_pattern": r.key_pattern}
        for r in rules
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ignore_rule(
    payload: IgnoreRuleCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create ignore rule."""
    ws = await require_workspace_role(
        db, UUID(payload.workspace_id), UUID(user_id), "admin"
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    rule = IgnoreRule(
        workspace_id=UUID(payload.workspace_id),
        type=payload.type,
        key_pattern=payload.key_pattern,
    )
    db.add(rule)
    await db.flush()
    return {
        "id": str(rule.id),
        "workspace_id": str(rule.workspace_id),
        "type": rule.type,
        "key_pattern": rule.key_pattern,
    }


@router.delete("/{rule_id}")
async def delete_ignore_rule(
    rule_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete ignore rule."""
    result = await db.execute(
        select(IgnoreRule).where(IgnoreRule.id == UUID(rule_id))
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    ws = await require_workspace_role(
        db, rule.workspace_id, UUID(user_id), "admin"
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await db.delete(rule)
    return {"message": "Deleted"}
