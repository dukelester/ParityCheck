"""View previously collected reports."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer


def run(
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Filter by environment"),
) -> None:
    """List cached reports from local .envguard directory."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    cache_dir = Path.home() / ".envguard"

    if not cache_dir.exists():
        typer.echo("No reports found. Run: envguard collect --env=dev")
        return

    reports = list(cache_dir.glob("report_*.json"))
    if env:
        reports = [r for r in reports if f"report_{env}.json" == r.name]

    table = Table(title="Cached Reports")
    table.add_column("Environment", style="cyan")
    table.add_column("Path", style="dim")
    table.add_column("Modified", style="green")

    for r in sorted(reports):
        env_name = r.stem.replace("report_", "")
        mtime = datetime.fromtimestamp(r.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        table.add_row(env_name, str(r), mtime)

    console.print(table)
