"""Report upload and retrieval endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_and_workspace, get_current_user_id
from app.core.utils import iso_utc
from app.db.models import Drift, Environment, Report, WorkspaceMember
from app.db.session import get_db
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_flow import process_report_upload

router = APIRouter()


def _deps_count(deps: dict | None) -> int:
    """Count packages in deps (handles structured or flat format)."""
    if not deps:
        return 0
    if isinstance(deps.get("installed_dependencies"), dict):
        return len(deps["installed_dependencies"])
    if isinstance(deps, dict) and not any(
        k in deps for k in ("direct_dependencies", "installed_dependencies", "transitive_dependencies")
    ):
        return len(deps)
    return len(deps.get("installed_dependencies") or deps.get("deps") or {})


def _format_os_summary(os_data: dict | None) -> str | None:
    """Format OS for summary, avoiding redundant 'Windows Windows' etc."""
    if not os_data:
        return None
    system = str(os_data.get("system", "")).strip()
    release = str(os_data.get("release", "")).strip()
    machine = str(os_data.get("machine", "")).strip()
    if not system and not release and not machine:
        return None
    if release and system and release.lower().startswith(system.lower()):
        parts = [release, machine]
    else:
        parts = [system, release, machine]
    return " ".join(p for p in parts if p).strip() or None


@router.post("/", response_model=ReportResponse)
async def create_report(
    payload: ReportCreate,
    auth: tuple[str, UUID | None] = Depends(get_current_user_and_workspace),
    db: AsyncSession = Depends(get_db),
) -> ReportResponse:
    """Receive report from CLI. Store in DB, compute drift, trigger alerts."""
    user_id, workspace_id = auth
    user_uuid = UUID(user_id)

    report_data = {
        "os": payload.os,
        "runtime": payload.runtime,
        "deps": payload.deps or {},
        "direct_dependencies": payload.direct_dependencies,
        "installed_dependencies": payload.installed_dependencies,
        "transitive_dependencies": payload.transitive_dependencies,
        "env_vars": payload.env_vars or {},
        "db_schema_hash": payload.db_schema_hash,
    }

    report, _ = await process_report_upload(
        db, user_uuid, workspace_id, payload.env, report_data
    )

    return ReportResponse(
        id=str(report.id),
        env=payload.env,
        timestamp=iso_utc(report.timestamp),
        status="stored",
        health_score=report.health_score,
    )


@router.get("/baseline")
async def get_baseline_report(
    auth: tuple[str, UUID | None] = Depends(get_current_user_and_workspace),
    db: AsyncSession = Depends(get_db),
) -> dict | None:
    """Get latest baseline report. Uses workspace from API key when present, else default."""
    from app.services.workspace import (
        get_latest_baseline_report,
        get_or_create_default_workspace,
    )

    user_id, workspace_id = auth
    ws_id = workspace_id
    if not ws_id:
        ws = await get_or_create_default_workspace(db, UUID(user_id))
        ws_id = ws.id
    report = await get_latest_baseline_report(db, ws_id)
    if not report:
        return None
    deps = report.deps or {}
    return {
        "id": str(report.id),
        "env": report.environment.name,
        "timestamp": iso_utc(report.timestamp),
        "os": report.os,
        "python_version": report.python_version,
        "deps": deps.get("installed_dependencies") or deps.get("deps") or deps,
        "direct_dependencies": deps.get("direct_dependencies"),
        "installed_dependencies": deps.get("installed_dependencies"),
        "transitive_dependencies": deps.get("transitive_dependencies"),
        "env_vars": report.env_vars or {},
        "db_schema_hash": report.db_schema_hash,
    }


@router.get("/")
async def list_reports(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    workspace_id: str | None = Query(None, description="Filter by workspace"),
    env: str | None = Query(None, description="Filter by environment name"),
    limit: int = Query(50, ge=1, le=100),
) -> list[dict]:
    """List reports for the current user."""
    from sqlalchemy.orm import selectinload

    user_uuid = UUID(user_id)
    from sqlalchemy import or_

    q = (
        select(Report)
        .join(Environment, Report.env_id == Environment.id)
        .options(selectinload(Report.environment))
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
        .order_by(Report.timestamp.desc())
        .limit(limit)
    )
    if workspace_id:
        q = q.where(Environment.workspace_id == UUID(workspace_id))
    if env:
        q = q.where(Environment.name == env)
    result = await db.execute(q)
    reports = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "env": r.environment.name,
            "timestamp": iso_utc(r.timestamp),
            "status": "stored",
            "health_score": r.health_score,
            "summary": {
                "os": _format_os_summary(r.os),
                "python_version": r.python_version,
                "deps_count": _deps_count(r.deps),
                "env_vars_count": len(r.env_vars) if r.env_vars else 0,
                "db_schema_hash": r.db_schema_hash,
            },
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

    from sqlalchemy import or_

    user_uuid = UUID(user_id)
    result = await db.execute(
        select(Report)
        .join(Environment, Report.env_id == Environment.id)
        .options(selectinload(Report.environment))
        .where(
            Report.id == UUID(report_id),
            or_(
                Environment.user_id == user_uuid,
                Environment.workspace_id.in_(
                    select(WorkspaceMember.workspace_id).where(
                        WorkspaceMember.user_id == user_uuid
                    )
                ),
            ),
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Backfill health_score for old reports that have null
    if report.health_score is None:
        from app.services.workspace import get_latest_baseline_report

        ws_id = report.environment.workspace_id
        if ws_id:
            baseline = await get_latest_baseline_report(db, ws_id)
            if baseline and baseline.env_id != report.env_id:
                from app.services.drift_engine import compare_reports
                from app.services.report_flow import _report_to_dict

                drift_result = compare_reports(
                    _report_to_dict(baseline),
                    _report_to_dict(report),
                )
                report.health_score = drift_result.health_score
            else:
                report.health_score = 100
        else:
            report.health_score = 100
        await db.flush()

    drift_result = await db.execute(
        select(Drift).where(Drift.report_id == report.id).order_by(Drift.created_at.desc())
    )
    drifts = drift_result.scalars().all()

    return {
        "id": str(report.id),
        "env": report.environment.name,
        "timestamp": iso_utc(report.timestamp),
        "health_score": report.health_score,
        "os": report.os,
        "python_version": report.python_version,
        "deps": report.deps,
        "env_vars": report.env_vars,
        "db_schema_hash": report.db_schema_hash,
        "drifts": [
            {
                "id": str(d.id),
                "type": d.type,
                "severity": d.severity,
                "key": d.key,
                "value_a": d.value_a,
                "value_b": d.value_b,
                "details": d.details or {},
            }
            for d in drifts
        ],
        "summary": {
            "critical": sum(1 for d in drifts if d.severity == "critical"),
            "high": sum(1 for d in drifts if d.severity == "high"),
            "medium": sum(1 for d in drifts if d.severity == "medium"),
            "low": sum(1 for d in drifts if d.severity == "low"),
        },
    }
