"""Compare current environment with baseline or other env."""

import json
from pathlib import Path
from typing import Optional

import typer


def _load_report(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _diff_dicts(a: dict, b: dict) -> tuple[list, list, list]:
    """Return (added, removed, changed) keys."""
    added = [k for k in b if k not in a]
    removed = [k for k in a if k not in b]
    changed = [k for k in a if k in b and a[k] != b[k]]
    return added, removed, changed


def run(
    env: str = typer.Option("prod", "--env", "-e", help="Environment to compare against"),
    baseline: Optional[str] = typer.Option(None, "--baseline", "-b", help="Baseline env (default: dev)"),
) -> None:
    """Compare current collected report with baseline or specified env."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    cache_dir = Path.home() / ".envguard"

    baseline_env = baseline or "dev"
    current_path = cache_dir / f"report_{env}.json"
    baseline_path = cache_dir / f"report_{baseline_env}.json"

    current = _load_report(current_path)
    base = _load_report(baseline_path)

    if not current:
        typer.echo(f"No report found for {env}. Run: envguard collect --env={env}", err=True)
        raise typer.Exit(1)
    if not base:
        typer.echo(f"No baseline found for {baseline_env}. Run: envguard collect --env={baseline_env}", err=True)
        raise typer.Exit(1)

    table = Table(title=f"Drift: {baseline_env} vs {env}")
    table.add_column("Category", style="cyan")
    table.add_column("Added", style="green")
    table.add_column("Removed", style="red")
    table.add_column("Changed", style="yellow")

    for category in ["deps", "env_vars"]:
        a, r, c = _diff_dicts(base.get(category, {}), current.get(category, {}))
        table.add_row(category, str(len(a)), str(len(r)), str(len(c)))

    # Runtime/OS
    if base.get("runtime", {}).get("python_version") != current.get("runtime", {}).get("python_version"):
        table.add_row("runtime", "Python version differs", "", "")
    if base.get("os") != current.get("os"):
        table.add_row("os", "OS differs", "", "")

    console.print(table)
