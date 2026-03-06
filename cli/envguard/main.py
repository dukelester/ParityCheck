"""ENVGUARD CLI entry point."""

import typer

from envguard import __version__
from envguard.commands import collect, compare, report, schedule, history, check, analyze

app = typer.Typer(
    name="envguard",
    help="Environment drift detection - collect, compare, and report to ParityCheck SaaS",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "-v",
        "--version",
        help="Show version and exit.",
    ),
    help_: bool = typer.Option(  # alias -h to help
        False,
        "-h",
        "--help",
        help="Show this message and exit.",
        is_eager=True,
    ),
) -> None:
    """ENVGUARD - Detect environment drift across dev, staging, prod."""
    if help_:
        typer.echo(ctx.get_help())
        raise typer.Exit()
    if version:
        typer.echo(f"envguard {__version__}")
        raise typer.Exit()
    # When called without a subcommand, show the top-level help.
    if not ctx.invoked_subcommand:
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.command("collect")(collect.run)
app.command("compare")(compare.run)
app.command("report")(report.run)
app.command("check")(check.run)
app.command("analyze")(analyze.run)
app.command("schedule")(schedule.run)
app.command("history")(history.run)


@app.command("version")
def version_cmd() -> None:
    """Show version."""
    typer.echo(f"envguard {__version__}")


if __name__ == "__main__":
    app()
