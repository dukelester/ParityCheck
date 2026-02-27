"""Schedule periodic drift checks via OS cron/task scheduler."""

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

import typer

CACHE_DIR = Path.home() / ".envguard"
SCHEDULE_FILE = CACHE_DIR / "schedule.json"

CRON_MAP = {"hourly": "0 * * * *", "daily": "0 9 * * *", "weekly": "0 9 * * 1"}


def run(
    interval: str = typer.Option(
        "daily", "--interval", "-i",
        help="Interval: hourly, daily, weekly",
    ),
    env: str = typer.Option(
        "dev", "--env", "-e",
        help="Environment to collect and report",
    ),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k",
        help="API key for report upload",
    ),
    install: bool = typer.Option(
        False, "--install",
        help="Install cron/task entry (Linux/macOS: crontab, Windows: schtasks)",
    ),
) -> None:
    """Configure and install scheduled drift detection."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "interval": interval,
        "env": env,
        "api_key": api_key,
    }
    SCHEDULE_FILE.write_text(json.dumps(config, indent=2))
    typer.echo(f"Schedule config saved: {interval} for env={env}")

    if install:
        if not api_key:
            typer.echo("--api-key required for --install", err=True)
            raise typer.Exit(1)
        cli_path = _get_cli_path()
        cron_expr = CRON_MAP.get(interval, CRON_MAP["daily"])
        cmd = f"{cli_path} collect --env={env} && {cli_path} report -k {api_key} --env={env}"
        if platform.system() in ("Linux", "Darwin"):
            _install_cron(cron_expr, cmd)
        elif platform.system() == "Windows":
            _install_windows_task(interval, cmd)
        else:
            typer.echo("Manual setup: add to crontab or Task Scheduler:", err=True)
            typer.echo(f"  {cron_expr} {cmd}")


def _get_cli_path() -> str:
    try:
        import envguard
        return f"{os.executable} -m envguard"
    except Exception:
        return "envguard"


def _install_cron(cron_expr: str, cmd: str) -> None:
    """Add cron entry."""
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
        )
        existing = result.stdout if result.returncode == 0 else ""
        new_line = f"{cron_expr} {cmd}\n"
        if new_line.strip() in existing:
            typer.echo("Cron entry already exists.")
            return
        updated = existing.rstrip() + "\n" + new_line if existing else new_line
        subprocess.run(["crontab", "-"], input=updated, check=True, text=True)
        typer.echo("Cron entry installed.")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Failed to install cron: {e}", err=True)
        raise typer.Exit(1)


def _install_windows_task(interval: str, cmd: str) -> None:
    """Add Windows Task Scheduler entry."""
    name = "ParityCheckEnvGuard"
    freq = {"hourly": "HOURLY", "daily": "DAILY", "weekly": "WEEKLY"}.get(interval, "DAILY")
    try:
        subprocess.run(
            [
                "schtasks", "/create", "/tn", name, "/tr", cmd,
                "/sc", freq, "/f",
            ],
            check=True,
            capture_output=True,
        )
        typer.echo("Task Scheduler entry installed.")
    except subprocess.CalledProcessError as e:
        typer.echo(f"Failed to install task: {e}", err=True)
        raise typer.Exit(1)
