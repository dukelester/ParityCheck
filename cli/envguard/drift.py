"""Local drift comparison (mirrors backend drift_engine)."""

from dataclasses import dataclass, field

SEVERITY_WEIGHTS = {"critical": 40, "high": 20, "medium": 10, "low": 3}
MAX_TOTAL_DEDUCTION = 90
CRITICAL_FLOOR = 30
SYSTEM_PACKAGES = {"pip", "setuptools", "wheel", "pkg-resources"}


@dataclass
class DriftEntry:
    type: str
    severity: str
    key: str | None = None
    value_a: str | None = None
    value_b: str | None = None
    details: dict = field(default_factory=dict)


@dataclass
class DriftResult:
    drifts: list[DriftEntry] = field(default_factory=list)
    health_score: int = 100
    summary: dict = field(default_factory=dict)


def _parse_version(ver: str) -> tuple[int, int, int]:
    import re
    try:
        from packaging.version import Version
        v = Version(ver.split()[0] if ver else "0")
        return (v.major, v.minor, v.micro) if hasattr(v, "major") else (0, 0, 0)
    except (ValueError, TypeError):
        parts = re.split(r"[\\.-]", str(ver).replace("*", "0"))[:3]
        return tuple(int(p) if p.isdigit() else 0 for p in (parts + [0, 0, 0])[:3])


def _version_severity(va: str, vb: str, _is_direct: bool = True) -> str:
    ma, mi, pa = _parse_version(va)
    mb, mj, pb = _parse_version(vb)
    if ma != mb:
        return "high"
    if mi != mj:
        return "medium"
    if pa != pb:
        return "low"
    return "low"


def _is_structured_deps(report: dict) -> bool:
    direct = report.get("direct_dependencies")
    trans = report.get("transitive_dependencies")
    return (
        isinstance(direct, dict) and direct is not None
    ) or (isinstance(trans, dict) and trans is not None)


def _compare_structured_dependencies(
    report_a: dict, report_b: dict, result: DriftResult
) -> None:
    direct_a = report_a.get("direct_dependencies") or {}
    direct_b = report_b.get("direct_dependencies") or {}
    trans_a = report_a.get("transitive_dependencies") or {}
    trans_b = report_b.get("transitive_dependencies") or {}

    def _add(k: str, sev: str, va: str | None, vb: str | None, cat: str, reason: str) -> None:
        if k in SYSTEM_PACKAGES:
            return
        result.drifts.append(
            DriftEntry(
                type="dependency",
                severity=sev,
                key=k,
                value_a=va,
                value_b=vb,
                details={"category": cat, "reason": reason},
            )
        )

    for pkg, ver_a in direct_a.items():
        if pkg in SYSTEM_PACKAGES:
            continue
        ver_b = direct_b.get(pkg)
        if ver_b is None:
            _add(pkg, "high", str(ver_a), None, "direct", "Missing direct dep")
        elif str(ver_a) != str(ver_b):
            sev = _version_severity(str(ver_a), str(ver_b))
            reason = "Major version mismatch" if sev == "high" else "Version mismatch"
            _add(pkg, sev, str(ver_a), str(ver_b), "direct", reason)

    for pkg in direct_b:
        if pkg not in direct_a and pkg not in SYSTEM_PACKAGES:
            _add(pkg, "medium", None, str(direct_b[pkg]), "direct", "New direct dep")

    if trans_a or trans_b:
        for pkg in set(trans_a) | set(trans_b):
            if pkg in SYSTEM_PACKAGES:
                continue
            va, vb = trans_a.get(pkg), trans_b.get(pkg)
            if va is None:
                _add(pkg, "low", None, str(vb), "transitive", "Transitive added")
            elif vb is None:
                _add(pkg, "low", str(va), None, "transitive", "Transitive removed")
            elif str(va) != str(vb):
                sev = _version_severity(str(va), str(vb))
                _add(pkg, sev, str(va), str(vb), "transitive", "Transitive version")


def _compare_legacy_dependencies(
    report_a: dict, report_b: dict, result: DriftResult
) -> None:
    deps_a = report_a.get("deps") or report_a.get("installed_dependencies") or {}
    deps_b = report_b.get("deps") or report_b.get("installed_dependencies") or {}
    for pkg in set(deps_a) | set(deps_b):
        if pkg in SYSTEM_PACKAGES:
            continue
        va, vb = deps_a.get(pkg), deps_b.get(pkg)
        if va is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency", severity="high", key=pkg,
                    value_a=None, value_b=str(vb),
                    details={"category": "legacy", "reason": "Added"},
                )
            )
        elif vb is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency", severity="high", key=pkg,
                    value_a=str(va), value_b=None,
                    details={"category": "legacy", "reason": "Removed"},
                )
            )
        elif str(va) != str(vb):
            sev = _version_severity(str(va), str(vb))
            result.drifts.append(
                DriftEntry(
                    type="dependency", severity=sev, key=pkg,
                    value_a=str(va), value_b=str(vb),
                    details={"category": "legacy", "reason": "Version mismatch"},
                )
            )


def compare_reports(report_a: dict, report_b: dict) -> DriftResult:
    """Compare two reports. report_a=baseline, report_b=current."""
    result = DriftResult()

    os_a, os_b = report_a.get("os") or {}, report_b.get("os") or {}
    if os_a != os_b:
        result.drifts.append(
            DriftEntry(
                type="runtime", severity="medium", key="os",
                value_a=str(os_a), value_b=str(os_b),
                details={"category": "os"},
            )
        )

    py_a = (report_a.get("runtime") or {}).get("python_version") or report_a.get("python_version")
    py_b = (report_b.get("runtime") or {}).get("python_version") or report_b.get("python_version")
    if py_a and py_b and py_a != py_b:
        sev = _version_severity(str(py_a), str(py_b))
        result.drifts.append(
            DriftEntry(
                type="runtime", severity=sev, key="python_version",
                value_a=str(py_a), value_b=str(py_b),
                details={"category": "python"},
            )
        )

    if _is_structured_deps(report_a) or _is_structured_deps(report_b):
        _compare_structured_dependencies(report_a, report_b, result)
    else:
        _compare_legacy_dependencies(report_a, report_b, result)

    ev_a = report_a.get("env_vars") or {}
    ev_b = report_b.get("env_vars") or {}
    for k in set(ev_a) | set(ev_b):
        va, vb = ev_a.get(k), ev_b.get(k)
        if va is None:
            result.drifts.append(
                DriftEntry("environment_variable", "high", k, None, str(vb))
            )
        elif vb is None:
            result.drifts.append(
                DriftEntry("environment_variable", "critical", k, str(va), None)
            )
        elif str(va) != str(vb):
            result.drifts.append(
                DriftEntry("environment_variable", "medium", k, str(va), str(vb))
            )

    h_a, h_b = report_a.get("db_schema_hash"), report_b.get("db_schema_hash")
    if h_a is not None and h_b is not None and h_a != h_b:
        result.drifts.append(
            DriftEntry("db_schema", "critical", "db_schema_hash", str(h_a), str(h_b))
        )

    total = sum(SEVERITY_WEIGHTS.get(d.severity, 10) for d in result.drifts)
    total = min(total, MAX_TOTAL_DEDUCTION)
    result.health_score = max(0, 100 - total)
    if any(d.severity == "critical" for d in result.drifts):
        result.health_score = min(result.health_score, CRITICAL_FLOOR)

    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for d in result.drifts:
        by_sev[d.severity] = by_sev.get(d.severity, 0) + 1
    result.summary = by_sev

    return result
