"""Collect environment metadata."""

import base64
import hashlib
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


def _is_inside_container() -> bool:
    """Check if we're running inside a Docker/LXC container."""
    return (Path("/.dockerenv").exists() or
            Path("/run/.containerenv").exists() or
            (Path("/proc/1/cgroup").exists() and
             "docker" in Path("/proc/1/cgroup").read_text()))


def _get_container_os() -> dict | None:
    """Read OS info from /etc/os-release inside container."""
    p = Path("/etc/os-release")
    if not p.exists():
        return None
    try:
        data = {}
        for line in p.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"')
        return {
            "id": data.get("ID", ""),
            "name": data.get("NAME", ""),
            "version": data.get("VERSION_ID", ""),
            "version_id": data.get("VERSION_ID", ""),
        } if data else None
    except Exception:
        return None


def _get_docker_metadata_from_inside() -> dict:
    """Collect Docker metadata when running inside a container."""
    import os
    out = {
        "image_tag": os.environ.get("CONTAINER_IMAGE") or os.environ.get("IMAGE") or
                     os.environ.get("DOCKER_IMAGE") or None,
        "image_digest": os.environ.get("IMAGE_DIGEST") or os.environ.get("CONTAINER_IMAGE_DIGEST") or None,
        "base_image": os.environ.get("BASE_IMAGE") or None,
        "container_os": _get_container_os(),
        "inside_container": True,
    }
    return {k: v for k, v in out.items() if v is not None or k == "inside_container"}


def _get_docker_metadata_from_host(container: str) -> dict | None:
    """Collect Docker metadata via docker inspect when run from host."""
    try:
        out = subprocess.run(
            ["docker", "inspect", container, "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0:
            return None
        data = json.loads(out.stdout)
        if isinstance(data, list):
            data = data[0] if data else {}
        img_id = data.get("Image", "")
        cid = (data.get("Id") or "")[:12]
        config = data.get("Config") or {}
        image_tag = config.get("Image") or img_id or "unknown"
        return {
            "image_tag": image_tag,
            "image_digest": img_id or cid,
            "base_image": None,
            "inside_container": False,
            "container_id": cid,
        }
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _get_docker_info(docker: bool, container: str | None) -> dict | None:
    """Get Docker metadata if --docker and (inside container or --container)."""
    if not docker:
        return None
    if container:
        return _get_docker_metadata_from_host(container)
    if _is_inside_container():
        return _get_docker_metadata_from_inside()
    return None


def _kubectl_get(namespace: str, resource: str, name: str | None = None) -> dict | list | None:
    """Run kubectl get and return JSON. Returns None on error."""
    cmd = ["kubectl", "get", resource, "-n", namespace, "-o", "json"]
    if name:
        cmd.extend([name])
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _hash_dict_data(data: dict) -> str:
    """Hash dict data for configmap/secret comparison. Sorts keys for stability."""
    if not data:
        return hashlib.sha256(b"").hexdigest()
    parts = []
    for k in sorted(data):
        v = data[k]
        if isinstance(v, str):
            parts.append(f"{k}={v}")
        else:
            parts.append(f"{k}={repr(v)}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _get_k8s_info(namespace: str, deployment: str | None) -> dict | None:
    """Collect K8s metadata: deployments, configmaps, secrets."""
    result: dict = {
        "namespace": namespace,
        "deployments": {},
        "configmaps": {},
        "secrets": {},
    }

    # Deployments
    deploy_list = _kubectl_get(namespace, "deployments")
    if deploy_list is None:
        return None
    items = deploy_list.get("items", []) if isinstance(deploy_list, dict) else deploy_list if isinstance(deploy_list, list) else []

    for dep in items:
        meta = dep.get("metadata", {})
        name = meta.get("name", "")
        if deployment and name != deployment:
            continue
        spec = dep.get("spec", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        containers = pod_spec.get("containers", [])
        dep_info: dict = {
            "replicas": spec.get("replicas"),
            "containers": [],
        }
        for c in containers:
            c_info: dict = {
                "name": c.get("name"),
                "image": c.get("image"),
                "resources": c.get("resources") or {},
            }
            env_vars = {}
            for e in c.get("env", []) or []:
                k = e.get("name")
                v = e.get("value")
                if k:
                    env_vars[k] = v if v is not None else "<from-envFrom>"
            if env_vars:
                c_info["env_vars"] = env_vars
            dep_info["containers"].append(c_info)
        result["deployments"][name] = dep_info

    # ConfigMaps
    cm_list = _kubectl_get(namespace, "configmaps")
    if cm_list:
        items = cm_list.get("items", []) if isinstance(cm_list, dict) else cm_list
        for cm in items:
            meta = cm.get("metadata", {})
            name = meta.get("name", "")
            data = cm.get("data", {}) or {}
            result["configmaps"][name] = {
                "data_hash": _hash_dict_data(data),
                "keys": sorted(data.keys()),
            }

    # Secrets
    secret_list = _kubectl_get(namespace, "secrets")
    if secret_list:
        items = secret_list.get("items", []) if isinstance(secret_list, dict) else secret_list
        for sec in items:
            meta = sec.get("metadata", {})
            name = meta.get("name", "")
            data = sec.get("data", {}) or {}
            # Decode base64 for hash (we don't store values)
            decoded = {}
            for k, v in data.items():
                try:
                    decoded[k] = base64.b64decode(v).hex() if v else ""
                except Exception:
                    decoded[k] = ""
            result["secrets"][name] = {
                "data_hash": _hash_dict_data(decoded),
                "keys": sorted(data.keys()),
            }

    return result


def run(
    env: str = typer.Option("dev", "--env", "-e", help="Environment name (dev/staging/prod)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Write report to file"),
    include_secrets: bool = typer.Option(False, "--include-secrets", help="Include secret env vars"),
    mode: str = typer.Option(
        "runtime",
        "--mode", "-m",
        help="Collection mode: runtime (virtualenv only) or full",
    ),
    docker: bool = typer.Option(
        False,
        "--docker",
        "-d",
        help="Collect Docker image metadata (tag, digest, base, OS)",
    ),
    container: Optional[str] = typer.Option(
        None,
        "--container",
        "-c",
        help="Container name/id when collecting from host (docker inspect)",
    ),
    k8s: bool = typer.Option(
        False,
        "--k8s",
        "-k",
        help="Collect Kubernetes metadata (deployments, configmaps, secrets)",
    ),
    namespace: str = typer.Option(
        "default",
        "--namespace",
        "-n",
        help="Kubernetes namespace (used with --k8s)",
    ),
    deployment: Optional[str] = typer.Option(
        None,
        "--deployment",
        help="Specific deployment name when using --k8s (default: all in namespace)",
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
    docker_info = _get_docker_info(docker, container)
    if docker_info:
        report_data["docker"] = docker_info

    k8s_info = _get_k8s_info(namespace, deployment) if k8s else None
    if k8s:
        if k8s_info:
            report_data["k8s"] = k8s_info
        else:
            typer.echo("Warning: kubectl failed or no cluster access. K8s metadata not collected.", err=True)

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
    if docker_info:
        table.add_row("Docker image", docker_info.get("image_tag") or "—")
        dig = docker_info.get("image_digest") or "—"
        table.add_row("Image digest", dig[:24] + "…" if len(dig) > 24 else dig)
        table.add_row("Base image", docker_info.get("base_image") or "—")
        if docker_info.get("container_os"):
            co = docker_info["container_os"]
            table.add_row("Container OS", f"{co.get('name', '')} {co.get('version_id', '')}".strip() or "—")
    if k8s_info:
        table.add_row("K8s namespace", k8s_info.get("namespace") or "—")
        dep_count = len(k8s_info.get("deployments") or {})
        cm_count = len(k8s_info.get("configmaps") or {})
        sec_count = len(k8s_info.get("secrets") or {})
        table.add_row("K8s deployments", str(dep_count))
        table.add_row("K8s configmaps", str(cm_count))
        table.add_row("K8s secrets", str(sec_count))
    console.print(table)

    cache_dir = Path.home() / ".envguard"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"report_{env}.json"
    cache_file.write_text(json.dumps(report_data, indent=2))
    typer.echo(f"Cached to {cache_file}")
