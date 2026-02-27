"""ENVGUARD CLI entry point."""

import typer

from envguard import __version__
from envguard.commands import collect, compare, report, schedule, history, check

app = typer.Typer(
    name="envguard",
    help="Environment drift detection - collect, compare, and report to ParityCheck SaaS",
    add_completion=False,
)


@app.callback()
def main() -> None:
    """ENVGUARD - Detect environment drift across dev, staging, prod."""
    pass


app.command("collect")(collect.run)
app.command("compare")(compare.run)
app.command("report")(report.run)
app.command("check")(check.run)
app.command("schedule")(schedule.run)
app.command("history")(history.run)


@app.command("version")
def version_cmd() -> None:
    """Show version."""
    typer.echo(f"envguard {__version__}")


if __name__ == "__main__":
    app()
