"""Upload report to ParityCheck SaaS API."""

import json
import os
from pathlib import Path
from typing import Optional

import httpx
import typer


DEFAULT_API_URL = "http://localhost:8000"


def run(
    api_key: str = typer.Option(..., "--api-key", "-k", help="API key for authentication"),
    env: str = typer.Option("dev", "--env", "-e", help="Environment name"),
    api_url: str = typer.Option(
        os.environ.get("PARITYCHECK_API_URL", DEFAULT_API_URL),
        "--api-url", "-u",
        help="API base URL (default: localhost:8000, or PARITYCHECK_API_URL env)",
    ),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Report file (default: use cached)"),
) -> None:
    """Upload report to ParityCheck SaaS."""
    cache_dir = Path.home() / ".envguard"
    report_path = Path(file) if file else cache_dir / f"report_{env}.json"

    if not report_path.exists():
        typer.echo(f"No report found. Run: envguard collect --env={env}", err=True)
        raise typer.Exit(1)

    data = json.loads(report_path.read_text())

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{api_url.rstrip('/')}/api/v1/reports/",
            json={"env": env, **data},
            headers={"Authorization": f"Bearer {api_key}", "X-API-Key": api_key},
        )

    if resp.status_code in (200, 201):
        typer.echo("Report uploaded successfully.")
    else:
        typer.echo(f"Upload failed: {resp.status_code} - {resp.text}", err=True)
        raise typer.Exit(1)
