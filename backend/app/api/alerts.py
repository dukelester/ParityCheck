"""Alert configuration (Slack, etc.)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import Alert
from app.db.session import get_db
from app.services.encryption import encrypt
from app.services.workspace import check_plan_limits, require_workspace_role

router = APIRouter()


class AlertCreate(BaseModel):
    workspace_id: str
    type: str = "slack"  # slack | email
    webhook_url: str | None = None
    email: str | None = None
    min_severity: str = "medium"


@router.get("/")
async def list_alerts(
    workspace_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List alerts for workspace (webhook URLs masked)."""
    ws = await require_workspace_role(db, UUID(workspace_id), UUID(user_id), "admin")
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = await db.execute(
        select(Alert).where(Alert.workspace_id == UUID(workspace_id))
    )
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "type": a.type,
            "min_severity": a.min_severity,
            "enabled": a.enabled,
            "webhook_configured": bool((a.config or {}).get("webhook_url")),
            "email_configured": bool((a.config or {}).get("email")),
        }
        for a in alerts
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create Slack alert."""
    ws = await require_workspace_role(
        db, UUID(payload.workspace_id), UUID(user_id), "admin"
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    alert_count = await db.scalar(
        select(func.count()).select_from(Alert).where(Alert.workspace_id == UUID(payload.workspace_id))
    )
    allowed, err = check_plan_limits(ws.plan, "create_alert", alert_count or 0)
    if not allowed:
        raise HTTPException(status_code=403, detail=err or "Plan limit")
    if payload.type == "slack":
        if not payload.webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url required for Slack alerts")
        config = {"webhook_url": encrypt(payload.webhook_url)}
    elif payload.type == "email":
        if not payload.email:
            raise HTTPException(status_code=400, detail="email required for email alerts")
        config = {"email": payload.email.strip().lower()}
    else:
        raise HTTPException(status_code=400, detail="type must be slack or email")
    alert = Alert(
        workspace_id=UUID(payload.workspace_id),
        type=payload.type,
        config=config,
        min_severity=payload.min_severity,
    )
    db.add(alert)
    await db.flush()
    return {
        "id": str(alert.id),
        "type": alert.type,
        "min_severity": alert.min_severity,
        "enabled": alert.enabled,
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete alert."""
    result = await db.execute(select(Alert).where(Alert.id == UUID(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    ws = await require_workspace_role(
        db, alert.workspace_id, UUID(user_id), "admin"
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    await db.delete(alert)
    return {"message": "Deleted"}
