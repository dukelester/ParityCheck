"""Collect environment metadata."""

import json
import platform
import sys
from pathlib import Path
from typing import Optional

import typer


def _get_os_info() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
    }


def _get_runtime_info() -> dict:
    return {
        "python_version": sys.version.split()[0],
        "executable": sys.executable,
    }


def _get_dependencies() -> dict:
    """Gather pip-installed packages (if available)."""
    try:
        import importlib.metadata

        dists = list(importlib.metadata.distributions())
        return {d.metadata["Name"]: d.version for d in dists if d.metadata.get("Name")}
    except Exception:
        return {}


def _get_env_vars(include_secrets: bool = False) -> dict:
    """Gather environment variables (redact secrets by default)."""
    import os

    sensitive = {"password", "secret", "key", "token", "credential"}
    result = {}
    for k, v in os.environ.items():
        if not include_secrets and any(s in k.lower() for s in sensitive):
            result[k] = "***REDACTED***"
        else:
            result[k] = v
    return result


def _get_db_schema_hash() -> str | None:
    """Placeholder: compute DB schema hash if DB connection available."""
    # TODO: Connect to DB, introspect schema, compute hash
    return None


def run(
    env: str = typer.Option("dev", "--env", "-e", help="Environment name (dev/staging/prod)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write report to file"),
    include_secrets: bool = typer.Option(False, "--include-secrets", help="Include secret env vars"),
) -> None:
    """Collect OS, runtime, dependencies, env vars, and DB schema hash."""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    report_data = {
        "env": env,
        "os": _get_os_info(),
        "runtime": _get_runtime_info(),
        "deps": _get_dependencies(),
        "env_vars": _get_env_vars(include_secrets=include_secrets),
        "db_schema_hash": _get_db_schema_hash(),
    }

    if output:
        Path(output).write_text(json.dumps(report_data, indent=2))
        typer.echo(f"Report saved to {output}")
        return

    table = Table(title=f"Environment: {env}")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="green")
    table.add_row("OS", f"{report_data['os']['system']} {report_data['os']['release']}")
    table.add_row("Python", report_data["runtime"]["python_version"])
    table.add_row("Dependencies", str(len(report_data["deps"])) + " packages")
    table.add_row("Env vars", str(len(report_data["env_vars"])) + " variables")
    table.add_row("DB schema hash", report_data["db_schema_hash"] or "N/A")
    console.print(table)

    # Store for compare/report (local cache)
    cache_dir = Path.home() / ".envguard"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"report_{env}.json"
    cache_file.write_text(json.dumps(report_data, indent=2))
    typer.echo(f"Cached to {cache_file}")
