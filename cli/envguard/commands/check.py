"""CI/CD check: compare with baseline, optionally fail on drift."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

import httpx
import typer

# Import drift engine logic (mirror of backend for local use)
from envguard.drift import compare_reports

DEFAULT_API_URL = "http://localhost:8000"

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def run(
    api_key: str = typer.Option(..., "--api-key", "-k", help="API key"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment to check"),
    api_url: str = typer.Option(
        os.environ.get("PARITYCHECK_API_URL", DEFAULT_API_URL),
        "--api-url", "-u",
        help="API base URL",
    ),
    fail_on_drift: bool = typer.Option(
        False, "--fail-on-drift", "-f",
        help="Exit 1 if drift severity >= min-severity",
    ),
    min_severity: str = typer.Option(
        "high", "--min-severity", "-m",
        help="Minimum severity to trigger fail (critical, high, medium, low)",
    ),
    file: Optional[str] = typer.Option(None, "--file", "-F", help="Report file"),
) -> None:
    """Compare current env with baseline. Use --fail-on-drift for CI/CD."""
    cache_dir = Path.home() / ".envguard"
    report_path = Path(file) if file else cache_dir / f"report_{env}.json"

    if not report_path.exists():
        typer.echo(f"No report for {env}. Run: envguard collect --env={env}", err=True)
        raise typer.Exit(1)

    current = json.loads(report_path.read_text())
    base_url = api_url.rstrip("/")

    with httpx.Client() as client:
        resp = client.get(
            f"{base_url}/api/v1/reports/baseline",
            headers={"Authorization": f"Bearer {api_key}", "X-API-Key": api_key},
        )

    if resp.status_code != 200:
        typer.echo(f"Failed to fetch baseline: {resp.status_code}", err=True)
        raise typer.Exit(1)

    baseline_data = resp.json()
    if not baseline_data:
        typer.echo("No baseline report. Upload a report from baseline env first.")
        raise typer.Exit(0)

    baseline = {
        "os": baseline_data.get("os"),
        "runtime": {"python_version": baseline_data.get("python_version")},
        "python_version": baseline_data.get("python_version"),
        "deps": baseline_data.get("deps") or {},
        "direct_dependencies": baseline_data.get("direct_dependencies"),
        "installed_dependencies": baseline_data.get("installed_dependencies"),
        "transitive_dependencies": baseline_data.get("transitive_dependencies"),
        "env_vars": baseline_data.get("env_vars") or {},
        "env_var_hashes": baseline_data.get("env_var_hashes") or {},
        "db_schema_hash": baseline_data.get("db_schema_hash"),
        "docker": baseline_data.get("docker"),
        "k8s": baseline_data.get("k8s"),
    }

    result = compare_reports(baseline, current)

    if not result.drifts:
        typer.echo("No drift detected.")
        raise typer.Exit(0)

    typer.echo(f"Drift detected: {len(result.drifts)} issue(s), health score {result.health_score}")
    for d in result.drifts:
        reason = f" – {d.details.get('reason', '')}" if d.details.get("reason") else ""
        cat = f" [{d.details.get('category', '')}]" if d.details.get("category") else ""
        typer.echo(f"  [{d.severity}]{cat} {d.type}: {d.key} ({d.value_a or '?'} -> {d.value_b or '?'}){reason}")

    if fail_on_drift:
        threshold = SEVERITY_ORDER.get(min_severity, 0)
        for d in result.drifts:
            if SEVERITY_ORDER.get(d.severity, 0) >= threshold:
                typer.echo(f"Failing: drift severity >= {min_severity}", err=True)
                raise typer.Exit(1)

    raise typer.Exit(0)
