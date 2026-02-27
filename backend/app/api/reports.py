"""Report upload and retrieval endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_id
from app.db.models import Environment, Report
from app.db.session import get_db
from app.schemas.report import ReportCreate, ReportResponse

router = APIRouter()


def _env_type_from_name(name: str) -> str:
    """Map env name to type (dev/staging/prod)."""
    n = name.lower()
    if n in ("dev", "development"):
        return "dev"
    if n in ("staging", "stage"):
        return "staging"
    if n in ("prod", "production"):
        return "prod"
    return "dev"


@router.post("/", response_model=ReportResponse)
async def create_report(
    payload: ReportCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Receive report from CLI. Store in DB and compute drift."""
    user_uuid = UUID(user_id)

    # Get or create environment
    result = await db.execute(
        select(Environment).where(
            Environment.user_id == user_uuid,
            Environment.name == payload.env,
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        env = Environment(
            user_id=user_uuid,
            name=payload.env,
            type=_env_type_from_name(payload.env),
        )
        db.add(env)
        await db.flush()

    python_version = None
    if payload.runtime and isinstance(payload.runtime, dict):
        python_version = payload.runtime.get("python_version") or payload.runtime.get("python")

    report = Report(
        env_id=env.id,
        os=payload.os,
        python_version=python_version,
        deps=payload.deps or {},
        env_vars=payload.env_vars or {},
        db_schema_hash=payload.db_schema_hash,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)

    return ReportResponse(
        id=str(report.id),
        env=payload.env,
        timestamp=report.timestamp.isoformat(),
        status="stored",
    )


@router.get("/")
async def list_reports(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    env: str | None = Query(None, description="Filter by environment name"),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict]:
    """List reports for the current user."""
    from sqlalchemy.orm import selectinload

    user_uuid = UUID(user_id)
    q = (
        select(Report)
        .join(Environment, Report.env_id == Environment.id)
        .where(Environment.user_id == user_uuid)
        .options(selectinload(Report.environment))
        .order_by(Report.timestamp.desc())
        .limit(limit)
    )
    if env:
        q = q.where(Environment.name == env)
    result = await db.execute(q)
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "env": r.environment.name,
            "timestamp": r.timestamp.isoformat(),
            "status": "stored",
        }
        for r in reports
    ]


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get report by ID."""
    from sqlalchemy.orm import selectinload

    user_uuid = UUID(user_id)
    result = await db.execute(
        select(Report)
        .join(Environment, Report.env_id == Environment.id)
        .where(Report.id == UUID(report_id), Environment.user_id == user_uuid)
        .options(selectinload(Report.environment))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {
        "id": str(report.id),
        "env": report.environment.name,
        "timestamp": report.timestamp.isoformat(),
        "os": report.os,
        "python_version": report.python_version,
        "deps": report.deps,
        "env_vars": report.env_vars,
        "db_schema_hash": report.db_schema_hash,
    }
