"""Real drift engine: compare reports and produce structured drift records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

# Severity weights for health score
SEVERITY_WEIGHTS = {"critical": 40, "high": 20, "medium": 10, "low": 5}

SENSITIVE_PATTERNS = {"password", "secret", "key", "token", "credential", "auth"}


def _is_sensitive_key(key: str) -> bool:
    k = key.lower()
    return any(p in k for p in SENSITIVE_PATTERNS)


def _mask_value(value: str) -> str:
    """Mask sensitive values for display."""
    if not value or len(value) < 4:
        return "***"
    return value[:2] + "***" + value[-2:] if len(value) > 4 else "***"


@dataclass
class DriftEntry:
    type: str  # runtime, dependency, environment_variable, db_schema
    severity: str  # critical, high, medium, low
    key: str | None = None
    value_a: str | None = None
    value_b: str | None = None
    details: dict = field(default_factory=dict)


@dataclass
class DriftResult:
    drifts: list[DriftEntry] = field(default_factory=list)
    health_score: int = 100

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
        }


def _matches_ignore(
    rule_type: str,
    key: str,
    ignore_rules: list[dict],
) -> bool:
    """Check if (type, key) matches any ignore rule."""
    for rule in ignore_rules:
        if rule.get("type") != rule_type:
            continue
        pattern = rule.get("key_pattern", "")
        if not pattern:
            continue
        if pattern == key:
            return True
        if "*" in pattern:
            re_pattern = pattern.replace("*", ".*")
            if re.fullmatch(re_pattern, key):
                return True
        try:
            if re.fullmatch(pattern, key):
                return True
        except re.error:
            pass
    return False


def compare_reports(
    report_a: dict,
    report_b: dict,
    ignore_rules: list[dict] | None = None,
) -> DriftResult:
    """
    Compare two reports and produce structured drift records.
    report_a = baseline, report_b = current.
    """
    ignore_rules = ignore_rules or []
    result = DriftResult()

    # --- Runtime drift ---
    os_a = report_a.get("os") or {}
    os_b = report_b.get("os") or {}
    py_a = (report_a.get("runtime") or {}).get("python_version") or report_a.get("python_version")
    py_b = (report_b.get("runtime") or {}).get("python_version") or report_b.get("python_version")

    if os_a != os_b and not _matches_ignore("runtime", "os", ignore_rules):
        result.drifts.append(
            DriftEntry(
                type="runtime",
                severity="medium",
                key="os",
                value_a=str(os_a),
                value_b=str(os_b),
                details={"category": "os"},
            )
        )

    if py_a and py_b and py_a != py_b:
        if _matches_ignore("runtime", "python_version", ignore_rules):
            pass
        else:
            va, vb = str(py_a), str(py_b)
            major_a = va.split(".")[0] if va else ""
            major_b = vb.split(".")[0] if vb else ""
            minor_a = va.split(".")[1] if len(va.split(".")) > 1 else ""
            minor_b = vb.split(".")[1] if len(vb.split(".")) > 1 else ""
            if major_a != major_b:
                sev = "high"
            elif minor_a != minor_b:
                sev = "medium"
            else:
                sev = "low"
            result.drifts.append(
                DriftEntry(
                    type="runtime",
                    severity=sev,
                    key="python_version",
                    value_a=va,
                    value_b=vb,
                    details={"category": "python"},
                )
            )

    # --- Dependency drift ---
    deps_a = report_a.get("deps") or {}
    deps_b = report_b.get("deps") or {}
    all_deps = set(deps_a) | set(deps_b)
    for pkg in all_deps:
        if _matches_ignore("dependency", pkg, ignore_rules):
            continue
        v_a = deps_a.get(pkg)
        v_b = deps_b.get(pkg)
        if v_a is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity="high",
                    key=pkg,
                    value_a=None,
                    value_b=str(v_b),
                    details={"change": "added"},
                )
            )
        elif v_b is None:
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity="high",
                    key=pkg,
                    value_a=str(v_a),
                    value_b=None,
                    details={"change": "removed"},
                )
            )
        elif str(v_a) != str(v_b):
            va, vb = str(v_a), str(v_b)
            parts_a = va.split(".")
            parts_b = vb.split(".")
            if len(parts_a) > 0 and len(parts_b) > 0 and parts_a[0] != parts_b[0]:
                sev = "high"
            elif len(parts_a) > 1 and len(parts_b) > 1 and parts_a[1] != parts_b[1]:
                sev = "medium"
            else:
                sev = "low"
            result.drifts.append(
                DriftEntry(
                    type="dependency",
                    severity=sev,
                    key=pkg,
                    value_a=va,
                    value_b=vb,
                    details={"change": "version"},
                )
            )

    # --- Environment variable drift ---
    ev_a = report_a.get("env_vars") or {}
    ev_b = report_b.get("env_vars") or {}
    all_ev = set(ev_a) | set(ev_b)
    for k in all_ev:
        if _matches_ignore("env_var", k, ignore_rules):
            continue
        v_a = ev_a.get(k)
        v_b = ev_b.get(k)
        if v_a is None:
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="high",
                    key=k,
                    value_a=None,
                    value_b=_mask_value(str(v_b)) if _is_sensitive_key(k) else str(v_b),
                    details={"change": "added"},
                )
            )
        elif v_b is None:
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="critical",
                    key=k,
                    value_a=_mask_value(str(v_a)) if _is_sensitive_key(k) else str(v_a),
                    value_b=None,
                    details={"change": "removed"},
                )
            )
        elif str(v_a) != str(v_b):
            display_a = _mask_value(str(v_a)) if _is_sensitive_key(k) else str(v_a)
            display_b = _mask_value(str(v_b)) if _is_sensitive_key(k) else str(v_b)
            result.drifts.append(
                DriftEntry(
                    type="environment_variable",
                    severity="medium",
                    key=k,
                    value_a=display_a,
                    value_b=display_b,
                    details={"change": "value"},
                )
            )

    # --- DB schema drift ---
    hash_a = report_a.get("db_schema_hash")
    hash_b = report_b.get("db_schema_hash")
    if hash_a is not None and hash_b is not None and hash_a != hash_b:
        if not _matches_ignore("db_schema", "db_schema_hash", ignore_rules):
            result.drifts.append(
                DriftEntry(
                    type="db_schema",
                    severity="critical",
                    key="db_schema_hash",
                    value_a=str(hash_a),
                    value_b=str(hash_b),
                    details={},
                )
            )

    # --- Health score ---
    total_weight = sum(SEVERITY_WEIGHTS.get(d.severity, 10) for d in result.drifts)
    result.health_score = max(0, 100 - total_weight)

    return result
