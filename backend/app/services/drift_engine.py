"""Drift engine: compare reports with direct/transitive dependency awareness."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Severity weights; low=3, cap total at 90
SEVERITY_WEIGHTS = {"critical": 40, "high": 20, "medium": 10, "low": 3}
MAX_TOTAL_DEDUCTION = 90
CRITICAL_FLOOR = 30

SYSTEM_PACKAGES = {"pip", "setuptools", "wheel", "pkg-resources"}

SENSITIVE_PATTERNS = {"password", "secret", "key", "token", "credential", "auth"}


def _is_sensitive_key(key: str) -> bool:
    return any(p in key.lower() for p in SENSITIVE_PATTERNS)


def _mask_value(value: str) -> str:
    if not value or len(value) < 4:
        return "***"
    return value[:2] + "***" + value[-2:] if len(value) > 4 else "***"


def _parse_version(ver: str) -> tuple[int, int, int]:
    """Parse version string to (major, minor, patch)."""
    try:
        from packaging.version import Version

        v = Version(ver.split()[0] if ver else "0")
        return (v.major, v.minor, v.micro) if hasattr(v, "major") else (0, 0, 0)
    except Exception:
        parts = re.split(r"[\\.-]", str(ver).replace("*", "0"))[:3]
        return tuple(int(p) if p.isdigit() else 0 for p in (parts + [0, 0, 0])[:3])


def _version_severity(va: str, vb: str, is_direct: bool) -> str:
    """Determine severity from version mismatch."""
    ma, mi, pa = _parse_version(va)
    mb, mj, pb = _parse_version(vb)
    if ma != mb:
        return "high"
    if mi != mj:
        return "medium" if is_direct else "medium"
    if pa != pb:
        return "low"
    return "low"


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

    def to_dict(self) -> dict:
        return {
            "drifts": [
                {
                    "type": d.type,
                    "severity": d.severity,
                    "key": d.key,
                    "value_a": d.value_a,
                    "value_b": d.value_b,
                    "details": d.details,
                }
                for d in self.drifts
            ],
            "health_score": self.health_score,
            "summary": self.summary,
        }


def _matches_ignore(rule_type: str, key: str, ignore_rules: list[dict]) -> bool:
    for rule in ignore_rules:
        if rule.get("type") != rule_type:
            continue
        pattern = rule.get("key_pattern", "")
        if not pattern:
            continue
        if pattern == key:
            return True
        if "*" in pattern:
            if re.fullmatch(pattern.replace("*", ".*"), key):
                return True
        try:
            if re.fullmatch(pattern, key):
                return True
        except re.error:
            pass
    return False


def _is_structured_deps(report: dict) -> bool:
    """Check if report has structured dependency format (direct/transitive)."""
    direct = report.get("direct_dependencies")
    trans = report.get("transitive_dependencies")
    return (isinstance(direct, dict) and direct is not None) or (
        isinstance(trans, dict) and trans is not None
    )


def _compare_structured_dependencies(
    report_a: dict,
    report_b: dict,
    result: DriftResult,
    ignore_rules: list[dict],
) -> None:
    """Compare dependencies with direct/transitive awareness."""
    direct_a = report_a.get("direct_dependencies") or {}
    direct_b = report_b.get("direct_dependencies") or {}
    installed_a = report_a.get("installed_dependencies") or report_a.get("deps") or {}
    installed_b = report_b.get("installed_dependencies") or report_b.get("deps") or {}
    trans_a = report_a.get("transitive_dependencies") or {}
    trans_b = report_b.get("transitive_dependencies") or {}

    def _add(key: str, sev: str, va: str | None, vb: str | None, category: str, reason: str) -> None:
        if _matches_ignore("dependency", key, ignore_rules):
            return
        if key in SYSTEM_PACKAGES:
            return
        result.drifts.append(
            DriftEntry(
                type="dependency",
                severity=sev,
                key=key,
                value_a=va,
                value_b=vb,
                details={"category": category, "reason": reason},
            )
        )

    # Direct deps: baseline vs target
    for pkg, ver_a in direct_a.items():
        if pkg in SYSTEM_PACKAGES:
            continue
        ver_b = direct_b.get(pkg)
        if ver_b is None:
            _add(pkg, "high", str(ver_a), None, "direct", "Missing direct dependency")
        elif str(ver_a) != str(ver_b):
            sev = _version_severity(str(ver_a), str(ver_b), True)
            reason = "Major version mismatch" if sev == "high" else "Version mismatch"
            _add(pkg, sev, str(ver_a), str(ver_b), "direct", reason)

    # New direct deps in target
    for pkg in direct_b:
        if pkg not in direct_a and pkg not in SYSTEM_PACKAGES:
            _add(pkg, "medium", None, str(direct_b[pkg]), "direct", "New direct dependency")

    # Transitive deps (only if both have structured data)
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
                sev = _version_severity(str(va), str(vb), False)
                _add(pkg, sev, str(va), str(vb), "transitive", "Transitive version mismatch")


def _compare_legacy_dependencies(
    report_a: dict,
    report_b: dict,
    result: DriftResult,
    ignore_rules: list[dict],
) -> None:
    """Fallback: flat deps comparison with system package filter."""
    deps_a = report_a.get("deps") or {}
    deps_b = report_b.get("deps") or {}
    for pkg in set(deps_a) | set(deps_b):
        if pkg in SYSTEM_PACKAGES or _matches_ignore("dependency", pkg, ignore_rules):
            continue
        va, vb = deps_a.get(pkg), deps_b.get(pkg)
        if va is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity="high",
                    key=pkg,
                    value_a=None,
                    value_b=str(vb),
                    details={"category": "legacy", "reason": "Added"},
                )
            )
        elif vb is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity="high",
                    key=pkg,
                    value_a=str(va),
                    value_b=None,
                    details={"category": "legacy", "reason": "Removed"},
                )
            )
        elif str(va) != str(vb):
            sev = _version_severity(str(va), str(vb), True)
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity=sev,
                    key=pkg,
                    value_a=str(va),
                    value_b=str(vb),
                    details={"category": "legacy", "reason": "Version mismatch"},
                )
            )


def compare_reports(
    report_a: dict,
    report_b: dict,
    ignore_rules: list[dict] | None = None,
) -> DriftResult:
    """Compare two reports. report_a=baseline, report_b=current."""
    ignore_rules = ignore_rules or []
    result = DriftResult()

    # Runtime
    os_a = report_a.get("os") or {}
    os_b = report_b.get("os") or {}
    py_a = (report_a.get("runtime") or {}).get("python_version") or report_a.get("python_version")
    py_b = (report_b.get("runtime") or {}).get("python_version") or report_b.get("python_version")

    if os_a != os_b and not _matches_ignore("runtime", "os", ignore_rules):
        result.drifts.append(
            DriftEntry(type="runtime", severity="medium", key="os", value_a=str(os_a), value_b=str(os_b), details={"category": "os"})
        )

    if py_a and py_b and py_a != py_b and not _matches_ignore("runtime", "python_version", ignore_rules):
        sev = _version_severity(str(py_a), str(py_b), True)
        result.drifts.append(
            DriftEntry(type="runtime", severity=sev, key="python_version", value_a=str(py_a), value_b=str(py_b), details={"category": "python"})
        )

    # Dependencies
    if _is_structured_deps(report_a) or _is_structured_deps(report_b):
        _compare_structured_dependencies(report_a, report_b, result, ignore_rules)
    else:
        _compare_legacy_dependencies(report_a, report_b, result, ignore_rules)

    # Env vars
    ev_a = report_a.get("env_vars") or {}
    ev_b = report_b.get("env_vars") or {}
    for k in set(ev_a) | set(ev_b):
        if _matches_ignore("env_var", k, ignore_rules):
            continue
        va, vb = ev_a.get(k), ev_b.get(k)
        if va is None:
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="high",
                    key=k,
                    value_a=None,
                    value_b=_mask_value(str(vb)) if _is_sensitive_key(k) else str(vb),
                    details={"change": "added"},
                )
            )
        elif vb is None:
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="critical",
                    key=k,
                    value_a=_mask_value(str(va)) if _is_sensitive_key(k) else str(va),
                    value_b=None,
                    details={"change": "removed"},
                )
            )
        elif str(va) != str(vb):
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="medium",
                    key=k,
                    value_a=_mask_value(str(va)) if _is_sensitive_key(k) else str(va),
                    value_b=_mask_value(str(vb)) if _is_sensitive_key(k) else str(vb),
                    details={"change": "value"},
                )
            )

    # DB schema
    hash_a, hash_b = report_a.get("db_schema_hash"), report_b.get("db_schema_hash")
    if hash_a is not None and hash_b is not None and hash_a != hash_b:
        if not _matches_ignore("db_schema", "db_schema_hash", ignore_rules):
            result.drifts.append(
                DriftEntry(type="db_schema", severity="critical", key="db_schema_hash", value_a=str(hash_a), value_b=str(hash_b), details={})
            )

    # Health score with cap
    total_weight = sum(SEVERITY_WEIGHTS.get(d.severity, 10) for d in result.drifts)
    total_weight = min(total_weight, MAX_TOTAL_DEDUCTION)
    result.health_score = max(0, 100 - total_weight)
    if any(d.severity == "critical" for d in result.drifts):
        result.health_score = min(result.health_score, CRITICAL_FLOOR)

    # Summary
    by_sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for d in result.drifts:
        by_sev[d.severity] = by_sev.get(d.severity, 0) + 1
    result.summary = by_sev

    return result
