"""Report upload flow: store, compare, drift, alert."""

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, Drift, Environment, IgnoreRule, Report, Workspace
from app.services.drift_engine import compare_reports
from app.services.email import send_drift_alert_email
from app.services.slack_alerts import send_slack_alert
from app.services.workspace import (
    get_baseline_environment,
    get_latest_baseline_report,
    get_or_create_default_workspace,
)


def _report_to_dict(report: Report) -> dict:
    """Convert Report model to dict for drift engine."""
    return {
        "os": report.os,
        "runtime": {"python_version": report.python_version} if report.python_version else {},
        "python_version": report.python_version,
        "deps": report.deps or {},
        "env_vars": report.env_vars or {},
        "db_schema_hash": report.db_schema_hash,
    }


async def process_report_upload(
    db: AsyncSession,
    user_id: UUID,
    workspace_id: UUID | None,
    env_name: str,
    report_data: dict,
) -> tuple[Report, list[dict]]:
    """
    Process report upload: create env if needed, compare with baseline,
    store drifts, compute health score. Returns (report, drifts).
    """
    ws_id = workspace_id
    if not ws_id:
        ws = await get_or_create_default_workspace(db, user_id)
        ws_id = ws.id

    result = await db.execute(
        select(Environment).where(
            Environment.workspace_id == ws_id,
            Environment.name == env_name,
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        legacy = await db.execute(
            select(Environment).where(
                Environment.user_id == user_id,
                Environment.name == env_name,
                Environment.workspace_id.is_(None),
            )
        )
        env = legacy.scalar_one_or_none()
        if env:
            env.workspace_id = ws_id
            env.user_id = None
            base = await get_baseline_environment(db, ws_id)
            if not base:
                env.is_baseline = True
            await db.flush()
    if not env:
        envs_result = await db.execute(
            select(Environment).where(Environment.workspace_id == ws_id)
        )
        existing = envs_result.scalars().all()
        env = Environment(
            workspace_id=ws_id,
            name=env_name,
            type=_env_type(env_name),
            is_baseline=len(existing) == 0,
        )
        db.add(env)
        await db.flush()

    python_version = None
    if report_data.get("runtime") and isinstance(report_data["runtime"], dict):
        python_version = (
            report_data["runtime"].get("python_version")
            or report_data["runtime"].get("python")
        )

    report = Report(
        env_id=env.id,
        os=report_data.get("os"),
        python_version=python_version,
        deps=report_data.get("deps") or {},
        env_vars=report_data.get("env_vars") or {},
        db_schema_hash=report_data.get("db_schema_hash"),
    )
    db.add(report)
    await db.flush()

    drifts_data: list[dict] = []
    baseline_report = await get_latest_baseline_report(db, ws_id)
    if not baseline_report:
        base = await get_baseline_environment(db, ws_id)
        if not base:
            first_env = await db.execute(
                select(Environment)
                .where(Environment.workspace_id == ws_id)
                .order_by(Environment.created_at, Environment.name)
                .limit(1)
            )
            first = first_env.scalar_one_or_none()
            if first:
                from sqlalchemy import update
                from sqlalchemy.orm import selectinload
                await db.execute(
                    update(Environment)
                    .where(Environment.workspace_id == ws_id)
                    .values(is_baseline=False)
                )
                first.is_baseline = True
                await db.flush()
                if first.id != env.id:
                    r = await db.execute(
                        select(Report)
                        .options(selectinload(Report.environment))
                        .where(Report.env_id == first.id)
                        .order_by(Report.timestamp.desc())
                        .limit(1)
                    )
                    baseline_report = r.scalar_one_or_none()
    if baseline_report and baseline_report.env_id != env.id:
        rules_result = await db.execute(
            select(IgnoreRule).where(IgnoreRule.workspace_id == ws_id)
        )
        rules = [
            {"type": r.type, "key_pattern": r.key_pattern}
            for r in rules_result.scalars().all()
        ]
        drift_result = compare_reports(
            _report_to_dict(baseline_report),
            _report_to_dict(report),
            ignore_rules=rules,
        )
        report.health_score = drift_result.health_score
        for d in drift_result.drifts:
            drift = Drift(
                report_id=report.id,
                type=d.type,
                severity=d.severity,
                key=d.key,
                value_a=d.value_a,
                value_b=d.value_b,
                details=d.details,
            )
            db.add(drift)
            drifts_data.append({
                "type": d.type,
                "severity": d.severity,
                "key": d.key,
                "value_a": d.value_a,
                "value_b": d.value_b,
            })
        await db.flush()

        alerts_result = await db.execute(
            select(Alert).where(
                Alert.workspace_id == ws_id,
                Alert.enabled == True,
                Alert.type.in_(["slack", "email"]),
            )
        )
        sev_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        for alert in alerts_result.scalars().all():
            min_order = sev_order.get(alert.min_severity, 0)
            if any(sev_order.get(d["severity"], 0) >= min_order for d in drifts_data):
                if alert.type == "slack":
                    webhook = (alert.config or {}).get("webhook_url")
                    if webhook:
                        asyncio.create_task(
                            send_slack_alert(
                                webhook,
                                env_name,
                                drift_result.health_score,
                                drifts_data,
                            )
                        )
                elif alert.type == "email":
                    email_addr = (alert.config or {}).get("email")
                    if email_addr:
                        asyncio.create_task(
                            send_drift_alert_email(
                                email_addr,
                                env_name,
                                drift_result.health_score,
                                drifts_data,
                            )
                        )
    else:
        report.health_score = 100

    await db.refresh(report)
    return report, drifts_data


def _env_type(name: str) -> str:
    n = name.lower()
    if n in ("dev", "development"):
        return "dev"
    if n in ("staging", "stage"):
        return "staging"
    if n in ("prod", "production"):
        return "prod"
    return "dev"
