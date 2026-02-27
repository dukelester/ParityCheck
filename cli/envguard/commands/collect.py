"""Collect environment metadata."""

import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer

SYSTEM_PACKAGES = {"pip", "setuptools", "wheel", "pkg-resources"}


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


def _parse_requirements_txt(path: Path) -> dict[str, str]:
    """Parse requirements.txt; return {name: constraint}."""
    result = {}
    try:
        text = path.read_text()
    except Exception:
        return result
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        # Match: package==1.2.3, package>=1.2, package
        m = re.match(r"^([a-zA-Z0-9_-]+)\s*(.*)$", line)
        if m:
            name = m.group(1).replace("_", "-").lower()
            constraint = m.group(2).strip() or "*"
            result[name] = constraint
    return result


def _parse_pyproject(path: Path) -> dict[str, str]:
    """Parse pyproject.toml for dependencies."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return {}
    try:
        data = tomllib.loads(path.read_text())
    except Exception:
        return {}
    result = {}
    # [project.dependencies] (PEP 621)
    deps = data.get("project", {}).get("dependencies", [])
    for dep in deps:
        if isinstance(dep, str):
            m = re.match(r"^([a-zA-Z0-9_-]+)\s*([\[<>=!~].*)?$", dep)
            if m:
                name = m.group(1).replace("_", "-").lower()
                result[name] = m.group(2).strip() if m.group(2) else "*"
    # [tool.poetry.dependencies]
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    for name, spec in poetry_deps.items():
        if name == "python":
            continue
        if isinstance(spec, dict):
            spec = spec.get("version", "*")
        result[name.replace("_", "-").lower()] = str(spec) if spec else "*"
    return result


def _parse_poetry_lock(path: Path) -> dict[str, str]:
    """Parse poetry.lock for package versions."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return {}
    try:
        data = tomllib.loads(path.read_text())
    except Exception:
        return {}
    result = {}
    for pkg in data.get("package", []):
        name = pkg.get("name", "").replace("_", "-").lower()
        version = pkg.get("version", "")
        if name:
            result[name] = version
    return result


def _get_direct_dependencies(cwd: Path) -> dict[str, str]:
    """Detect direct deps: poetry.lock > pyproject.toml > requirements.txt."""
    if (cwd / "poetry.lock").exists():
        direct = _parse_poetry_lock(cwd / "poetry.lock")
        if direct:
            return direct
    if (cwd / "pyproject.toml").exists():
        direct = _parse_pyproject(cwd / "pyproject.toml")
        if direct:
            return direct
    for name in ("requirements.txt", "requirements.in"):
        p = cwd / name
        if p.exists():
            return _parse_requirements_txt(p)
    return {}


def _get_installed_dependencies(mode: str) -> dict[str, str]:
    """Get installed packages via pip list --format=json."""
    try:
        out = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=Path.cwd(),
        )
        if out.returncode != 0:
            return {}
        data = json.loads(out.stdout)
        result = {}
        for pkg in data:
            name = (pkg.get("name") or "").replace("_", "-").lower()
            version = pkg.get("version", "")
            if name and name not in SYSTEM_PACKAGES:
                result[name] = version
        return result
    except Exception:
        return {}


def _extract_version_from_constraint(constraint: str) -> str | None:
    """Extract pinned version from constraint like ==4.2.5 or >=2.30."""
    if not constraint or constraint == "*":
        return None
    m = re.match(r"^==\s*(.+)$", constraint.strip())
    if m:
        return m.group(1).strip()
    return None


def _get_dependencies(cwd: Path, mode: str) -> dict:
    """
    Return structured deps:
    {
      "direct_dependencies": {},
      "installed_dependencies": {},
      "transitive_dependencies": {}
    }
    Also include legacy "deps" for backward compatibility.
    """
    direct = _get_direct_dependencies(cwd)
    installed = _get_installed_dependencies(mode)

    transitive = {}
    for name, version in installed.items():
        if name not in direct:
            transitive[name] = version

    legacy_deps = {**direct, **transitive}

    return {
        "direct_dependencies": direct,
        "installed_dependencies": installed,
        "transitive_dependencies": transitive,
        "deps": legacy_deps,
    }


def _get_env_vars(include_secrets: bool = False) -> dict:
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
    return None


def _is_inside_venv() -> bool:
    """Check if we're inside a virtualenv."""
    return sys.prefix != sys.base_prefix


def run(
    env: str = typer.Option("dev", "--env", "-e", help="Environment name (dev/staging/prod)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write report to file"),
    include_secrets: bool = typer.Option(False, "--include-secrets", help="Include secret env vars"),
    mode: str = typer.Option(
        "runtime",
        "--mode", "-m",
        help="Collection mode: runtime (virtualenv only) or full",
    ),
) -> None:
    """Collect OS, runtime, dependencies, env vars, and DB schema hash."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    cwd = Path.cwd()

    if mode == "runtime" and not _is_inside_venv():
        typer.echo("Warning: Not inside a virtualenv. Run from project venv for accurate deps.", err=True)

    deps_data = _get_dependencies(cwd, mode)

    report_data = {
        "env": env,
        "os": _get_os_info(),
        "runtime": _get_runtime_info(),
        "deps": deps_data.get("deps", {}),
        "direct_dependencies": deps_data.get("direct_dependencies", {}),
        "installed_dependencies": deps_data.get("installed_dependencies", {}),
        "transitive_dependencies": deps_data.get("transitive_dependencies", {}),
        "env_vars": _get_env_vars(include_secrets=include_secrets),
        "db_schema_hash": _get_db_schema_hash(),
    }

    if output:
        Path(output).write_text(json.dumps(report_data, indent=2))
        typer.echo(f"Report saved to {output}")
        return

    direct_count = len(report_data.get("direct_dependencies") or {})
    installed_count = len(report_data.get("installed_dependencies") or {})
    trans_count = len(report_data.get("transitive_dependencies") or {})

    table = Table(title=f"Environment: {env}")
    table.add_column("Category", style="cyan")
    table.add_column("Details", style="green")
    table.add_row("OS", f"{report_data['os']['system']} {report_data['os']['release']}")
    table.add_row("Python", report_data["runtime"]["python_version"])
    table.add_row("Direct deps", str(direct_count))
    table.add_row("Installed deps", str(installed_count))
    table.add_row("Transitive deps", str(trans_count))
    table.add_row("Env vars", str(len(report_data["env_vars"])) + " variables")
    table.add_row("DB schema hash", report_data["db_schema_hash"] or "N/A")
    console.print(table)

    cache_dir = Path.home() / ".envguard"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"report_{env}.json"
    cache_file.write_text(json.dumps(report_data, indent=2))
    typer.echo(f"Cached to {cache_file}")
