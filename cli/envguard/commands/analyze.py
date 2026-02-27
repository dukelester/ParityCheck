"""Deployment risk analysis: compare PR/branch vs production baseline."""

import json
import os
from pathlib import Path
from typing import Optional

import httpx
import typer

from envguard.drift import compare_reports

DEFAULT_API_URL = "http://localhost:8000"

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _risk_level(score: int) -> str:
    if score <= 20:
        return "Low"
    if score <= 50:
        return "Medium"
    return "High"


def _format_baseline(baseline_data: dict) -> dict:
    """Convert API response to drift-comparable dict."""
    deps = baseline_data.get("deps") or {}
    return {
        "os": baseline_data.get("os"),
        "runtime": {"python_version": baseline_data.get("python_version")},
        "python_version": baseline_data.get("python_version"),
        "deps": deps,
        "direct_dependencies": baseline_data.get("direct_dependencies"),
        "installed_dependencies": baseline_data.get("installed_dependencies"),
        "transitive_dependencies": baseline_data.get("transitive_dependencies"),
        "env_vars": baseline_data.get("env_vars") or {},
        "env_var_hashes": baseline_data.get("env_var_hashes") or {},
        "db_schema_hash": baseline_data.get("db_schema_hash"),
        "docker": baseline_data.get("docker"),
        "k8s": baseline_data.get("k8s"),
    }


def run(
    against: str = typer.Option(
        "prod",
        "--against",
        "-a",
        help="Environment to compare against (e.g. prod, staging)",
    ),
    env: str = typer.Option(
        "dev",
        "--env",
        "-e",
        help="Current env / branch name (report from collect)",
    ),
    api_key: str = typer.Option(..., "--api-key", "-k", help="API key for auth"),
    api_url: str = typer.Option(
        os.environ.get("PARITYCHECK_API_URL", DEFAULT_API_URL),
        "--api-url",
        "-u",
        help="API base URL",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-F",
        help="Report file (default: use cached report for --env)",
    ),
    output: str = typer.Option(
        "text",
        "--output",
        "-o",
        help="Output format: text or json",
    ),
    fail_on_risk: bool = typer.Option(
        False,
        "--fail-on-risk",
        "-f",
        help="Exit 1 if deployment risk above threshold",
    ),
    risk_threshold: int = typer.Option(
        50,
        "--risk-threshold",
        "-t",
        help="Risk score threshold for --fail-on-risk (0-100)",
    ),
) -> None:
    """Analyze deployment risk: compare current env vs production baseline."""
    cache_dir = Path.home() / ".envguard"
    report_path = Path(file) if file else cache_dir / f"report_{env}.json"

    if not report_path.exists():
        typer.echo(
            f"No report for {env}. Run: envguard collect --env={env}",
            err=True,
        )
        raise typer.Exit(1)

    current = json.loads(report_path.read_text(encoding="utf-8"))
    base_url = api_url.rstrip("/")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            f"{base_url}/api/v1/reports/latest?env={against}",
            headers={"Authorization": f"Bearer {api_key}", "X-API-Key": api_key},
        )

    if resp.status_code != 200:
        typer.echo(
            f"Failed to fetch {against} baseline: {resp.status_code}",
            err=True,
        )
        raise typer.Exit(1)

    baseline_data = resp.json()
    if not baseline_data:
        typer.echo(
            f"No report for {against}. Upload from {against} first.",
            err=True,
        )
        raise typer.Exit(1)

    baseline = _format_baseline(baseline_data)
    result = compare_reports(baseline, current)

    risk_score = 100 - result.health_score
    level = _risk_level(risk_score)
    safe = result.health_score == 100

    out = {
        "deployment_risk_score": risk_score,
        "health_score": result.health_score,
        "risk_level": level,
        "safe_to_deploy": safe,
        "against": against,
        "current_env": env,
        "drift_count": len(result.drifts),
        "summary": result.summary,
        "risky_changes": [
            {
                "severity": d.severity,
                "type": d.type,
                "key": d.key,
                "value_a": d.value_a,
                "value_b": d.value_b,
                "category": d.details.get("category"),
                "reason": d.details.get("reason"),
            }
            for d in result.drifts
        ],
    }

    if output == "json":
        typer.echo(json.dumps(out, indent=2))
    else:
        typer.echo("")
        typer.echo("Deployment Risk Analysis")
        typer.echo("=" * 40)
        typer.echo(f"Comparing: {env} → {against}")
        typer.echo("")
        typer.echo(f"Deployment Risk: {risk_score}/100 ({level})")
        typer.echo(f"Health Score: {result.health_score}/100")
        typer.echo("")
        if safe:
            typer.echo("Safe to deploy: Yes – no drift detected")
        else:
            typer.echo("Safe to deploy: No – drift detected")
            typer.echo("")
            typer.echo("Risky changes vs production:")
            for d in result.drifts:
                cat = f" [{d.details.get('category', '')}]" if d.details.get("category") else ""
                reason = f" – {d.details.get('reason', '')}" if d.details.get("reason") else ""
                va = d.value_a or "?"
                vb = d.value_b or "?"
                typer.echo(f"  [{d.severity}]{cat} {d.key}: {va} → {vb}{reason}")
        typer.echo("")

    if fail_on_risk and risk_score >= risk_threshold:
        typer.echo(
            f"Failing: deployment risk {risk_score} >= {risk_threshold}",
            err=True,
        )
        raise typer.Exit(1)

    raise typer.Exit(0)
