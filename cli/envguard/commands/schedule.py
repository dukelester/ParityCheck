"""Schedule periodic drift checks (paid feature)."""

from typing import Optional

import typer


def run(
    interval: str = typer.Option("daily", "--interval", "-i", help="Interval: hourly, daily, weekly"),
    notify: bool = typer.Option(False, "--notify", "-n", help="Enable Slack/email alerts"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API key (required for notify)"),
) -> None:
    """Configure scheduled drift detection (requires Pro/Enterprise)."""
    typer.echo(
        f"Schedule: {interval}, notify={notify}. "
        "Configure via SaaS dashboard or CI cron job for full automation."
    )
    if notify and not api_key:
        typer.echo("--api-key required when --notify is set.", err=True)
