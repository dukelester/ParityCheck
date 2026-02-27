"""Workspace and plan management."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Environment, Report, Workspace, WorkspaceMember

# Plan limits (slack_alerts = max number of alerts, 0 = none)
PLAN_LIMITS = {
    "free": {"workspaces": 1, "environments": 2, "history_days": 7, "slack_alerts": 1},
    "pro": {"workspaces": 5, "environments": 10, "history_days": 90, "slack_alerts": 10},
    "enterprise": {"workspaces": 999, "environments": 999, "history_days": 365, "slack_alerts": 999},
}


async def get_or_create_default_workspace(
    db: AsyncSession, user_id: UUID
) -> Workspace:
    """Get user's default (first) workspace or create one."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at)
        .limit(1)
    )
    ws = result.scalar_one_or_none()
    if ws:
        return ws
    ws = Workspace(name="My Workspace", owner_id=user_id, plan="free")
    db.add(ws)
    await db.flush()
    member = WorkspaceMember(workspace_id=ws.id, user_id=user_id, role="owner")
    db.add(member)
    await db.flush()
    return ws


async def get_workspace_for_user(
    db: AsyncSession, workspace_id: UUID, user_id: UUID
) -> Workspace | None:
    """Get workspace if user has access."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            Workspace.id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def require_workspace_role(
    db: AsyncSession, workspace_id: UUID, user_id: UUID, min_role: str
) -> Workspace | None:
    """Require user has at least min_role (owner > admin > member)."""
    ws = await get_workspace_for_user(db, workspace_id, user_id)
    if not ws:
        return None
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        return None
    order = {"owner": 3, "admin": 2, "member": 1}
    if order.get(member.role, 0) < order.get(min_role, 0):
        return None
    return ws


async def get_baseline_environment(
    db: AsyncSession, workspace_id: UUID
) -> Environment | None:
    """Get the baseline environment for a workspace."""
    result = await db.execute(
        select(Environment).where(
            Environment.workspace_id == workspace_id,
            Environment.is_baseline == True,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_baseline_report(
    db: AsyncSession, workspace_id: UUID
) -> Report | None:
    """Get latest report from baseline environment."""
    from sqlalchemy.orm import selectinload

    base = await get_baseline_environment(db, workspace_id)
    if not base:
        return None
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.environment))
        .where(Report.env_id == base.id)
        .order_by(Report.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def set_baseline(
    db: AsyncSession, workspace_id: UUID, env_id: UUID, user_id: UUID
) -> bool:
    """Set environment as baseline. Only one per workspace."""
    ws = await require_workspace_role(db, workspace_id, user_id, "admin")
    if not ws:
        return False
    result = await db.execute(
        select(Environment).where(
            Environment.workspace_id == workspace_id,
            Environment.id == env_id,
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        return False
    from sqlalchemy import update

    await db.execute(
        update(Environment)
        .where(Environment.workspace_id == workspace_id)
        .values(is_baseline=False)
    )
    env.is_baseline = True
    await db.flush()
    return True


def check_plan_limits(
    plan: str, action: str, current_count: int
) -> tuple[bool, str | None]:
    """
    Check if action is allowed under plan.
    Returns (allowed, error_message).
    """
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
    if action == "create_environment":
        max_env = limits["environments"]
        if current_count >= max_env:
            return False, f"Plan limit: max {max_env} environments"
    if action == "create_workspace":
        max_ws = limits["workspaces"]
        if current_count >= max_ws:
            return False, f"Plan limit: max {max_ws} workspaces"
    if action == "create_alert":
        max_alerts = limits.get("slack_alerts", 0)
        if max_alerts <= 0:
            return False, "Slack alerts require Pro plan"
        if current_count >= max_alerts:
            return False, f"Plan limit: max {max_alerts} Slack alert(s)"
    return True, None
