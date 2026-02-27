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

WEAK_SECRET_VALUES = {
    "secret", "dev", "changeme", "default", "xxx", "123", "password",
    "django-insecure-", "insecure", "test", "demo", "temp", "tmp",
}


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


def _check_security(
    report: dict,
    result: DriftResult,
    ignore_rules: list[dict],
) -> None:
    """Weak config, DEBUG in prod, AWS S3 public bucket advisory."""
    ev = report.get("env_vars") or {}
    env_name = (report.get("env") or "").lower()

    # DEBUG=True in prod
    if "prod" in env_name or "production" in env_name:
        debug_val = ev.get("DEBUG", ev.get("DJANGO_DEBUG", "")).lower()
        if debug_val in ("true", "1", "yes"):
            if not _matches_ignore("config", "DEBUG", ignore_rules):
                result.drifts.append(
                    DriftEntry(
                        type="config",
                        severity="critical",
                        key="DEBUG",
                        value_a=None,
                        value_b="True",
                        details={"category": "security", "reason": "DEBUG enabled in production"},
                    )
                )

    # Weak SECRET_KEY / similar
    for key in ev:
        if "secret" in key.lower() or key in ("SECRET_KEY", "DJANGO_SECRET_KEY"):
            v = str(ev.get(key, "")).lower()
            if v and v != "***redacted***":
                for weak in WEAK_SECRET_VALUES:
                    if weak in v or v == weak:
                        if not _matches_ignore("config", key, ignore_rules):
                            result.drifts.append(
                                DriftEntry(
                                    type="config",
                                    severity="high",
                                    key=key,
                                    value_a=None,
                                    value_b=_mask_value(v),
                                    details={"category": "weak_config", "reason": "Weak secret value"},
                                )
                            )
                        break

    # AWS creds detected -> S3 public bucket audit advisory
    if ev.get("AWS_ACCESS_KEY_ID") or ev.get("AWS_SECRET_ACCESS_KEY"):
        if not _matches_ignore("config", "AWS_S3_AUDIT", ignore_rules):
            result.drifts.append(
                DriftEntry(
                    type="config",
                    severity="medium",
                    key="AWS_CREDENTIALS",
                    value_a=None,
                    value_b="present",
                    details={
                        "category": "security",
                        "reason": "AWS credentials detected - audit S3 bucket public access",
                    },
                )
            )


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
    required_by = (report_b.get("deps") or {}).get("required_by") or {}
    if trans_a or trans_b:
        for pkg in set(trans_a) | set(trans_b):
            if pkg in SYSTEM_PACKAGES:
                continue
            va, vb = trans_a.get(pkg), trans_b.get(pkg)
            likely = required_by.get(pkg)
            details_extra = {"likely_caused_by": likely} if likely else {}
            if va is None:
                de = DriftEntry(
                    type="dependency",
                    severity="low",
                    key=pkg,
                    value_a=None,
                    value_b=str(vb),
                    details={"category": "transitive", "reason": "Transitive added", **details_extra},
                )
                result.drifts.append(de)
            elif vb is None:
                de = DriftEntry(
                    type="dependency",
                    severity="low",
                    key=pkg,
                    value_a=str(va),
                    value_b=None,
                    details={"category": "transitive", "reason": "Transitive removed", **details_extra},
                )
                result.drifts.append(de)
            elif str(va) != str(vb):
                sev = _version_severity(str(va), str(vb), False)
                de = DriftEntry(
                    type="dependency",
                    severity=sev,
                    key=pkg,
                    value_a=str(va),
                    value_b=str(vb),
                    details={"category": "transitive", "reason": "Transitive version mismatch", **details_extra},
                )
                result.drifts.append(de)


def _compare_k8s(
    k8s_a: dict,
    k8s_b: dict,
    result: DriftResult,
    ignore_rules: list[dict],
) -> None:
    """Compare K8s deployments, configmaps, secrets."""
    def _add(t: str, sev: str, key: str, va: Any, vb: Any, reason: str) -> None:
        if _matches_ignore("k8s", key, ignore_rules):
            return
        result.drifts.append(
            DriftEntry(
                type="k8s",
                severity=sev,
                key=key,
                value_a=str(va) if va is not None else None,
                value_b=str(vb) if vb is not None else None,
                details={"category": "k8s", "reason": reason},
            )
        )

    # ConfigMaps: compare by name and data_hash
    cm_a = k8s_a.get("configmaps") or {}
    cm_b = k8s_b.get("configmaps") or {}
    for name in set(cm_a) | set(cm_b):
        ha, hb = (cm_a.get(name) or {}).get("data_hash"), (cm_b.get(name) or {}).get("data_hash")
        if ha is None:
            _add("k8s", "high", f"configmap:{name}", None, hb, "ConfigMap added")
        elif hb is None:
            _add("k8s", "high", f"configmap:{name}", ha, None, "ConfigMap removed")
        elif ha != hb:
            _add("k8s", "high", f"configmap:{name}", ha, hb, "ConfigMap data changed")

    # Secrets: compare by name and data_hash
    sec_a = k8s_a.get("secrets") or {}
    sec_b = k8s_b.get("secrets") or {}
    for name in set(sec_a) | set(sec_b):
        ha, hb = (sec_a.get(name) or {}).get("data_hash"), (sec_b.get(name) or {}).get("data_hash")
        if ha is None:
            _add("k8s", "critical", f"secret:{name}", None, hb, "Secret added")
        elif hb is None:
            _add("k8s", "critical", f"secret:{name}", ha, None, "Secret removed")
        elif ha != hb:
            _add("k8s", "critical", f"secret:{name}", ha, hb, "Secret data changed")

    # Deployments: image, replicas, resources, env_vars
    dep_a = k8s_a.get("deployments") or {}
    dep_b = k8s_b.get("deployments") or {}
    for name in set(dep_a) | set(dep_b):
        da, db = dep_a.get(name) or {}, dep_b.get(name) or {}
        if not da:
            _add("k8s", "high", f"deployment:{name}", None, "present", "Deployment added")
            continue
        if not db:
            _add("k8s", "high", f"deployment:{name}", "present", None, "Deployment removed")
            continue

        # Replicas
        ra, rb = da.get("replicas"), db.get("replicas")
        if ra is not None and rb is not None and ra != rb:
            _add("k8s", "medium", f"deployment:{name}.replicas", ra, rb, "Replica count changed")

        # Containers: image, resources, env_vars
        ca_list = da.get("containers") or []
        cb_list = db.get("containers") or []
        cb_by_name = {c.get("name"): c for c in cb_list if c.get("name")}
        for ca in ca_list:
            cname = ca.get("name", "")
            cb = cb_by_name.get(cname) if cname else (cb_list[0] if cb_list else {})
            prefix = f"deployment:{name}.{cname}" if cname else f"deployment:{name}"

            img_a, img_b = ca.get("image"), cb.get("image") if cb else None
            if img_a and img_b and img_a != img_b:
                _add("k8s", "high", f"{prefix}.image", img_a, img_b, "Image tag changed")

            res_a = ca.get("resources") or {}
            res_b = cb.get("resources") or {} if cb else {}
            limits_a = res_a.get("limits") or {}
            limits_b = res_b.get("limits") or {}
            if limits_a != limits_b:
                _add("k8s", "medium", f"{prefix}.limits", str(limits_a), str(limits_b), "Resource limits changed")
            req_a = res_a.get("requests") or {}
            req_b = res_b.get("requests") or {}
            if req_a != req_b:
                _add("k8s", "low", f"{prefix}.requests", str(req_a), str(req_b), "Resource requests changed")

            ev_a = ca.get("env_vars") or {}
            ev_b = cb.get("env_vars") or {} if cb else {}
            for k in set(ev_a) | set(ev_b):
                va, vb = ev_a.get(k), ev_b.get(k)
                if va != vb:
                    _add("k8s", "medium", f"{prefix}.env.{k}", va, vb, "Env var changed")


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
    hash_a = report_a.get("env_var_hashes") or {}
    hash_b = report_b.get("env_var_hashes") or {}
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
        elif _is_sensitive_key(k) and hash_a.get(k) and hash_b.get(k):
            if hash_a.get(k) != hash_b.get(k) and not _matches_ignore(
                "secret_drift", k, ignore_rules
            ) and not _matches_ignore("env_var", k, ignore_rules):
                result.drifts.append(
                    DriftEntry(
                        type="secret_drift",
                        severity="critical",
                        key=k,
                        value_a="***",
                        value_b="***",
                        details={"change": "value", "reason": "Secret value changed"},
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

    # Security checks (run on report_b / current)
    _check_security(report_b, result, ignore_rules)

    # Docker
    docker_a = report_a.get("docker") or {}
    docker_b = report_b.get("docker") or {}
    if docker_a or docker_b:
        for key, label, sev in [
            ("image_digest", "Image digest", "high"),
            ("base_image", "Base image", "high"),
            ("image_tag", "Image tag", "medium"),
            ("container_os", "Container OS", "medium"),
        ]:
            va, vb = docker_a.get(key), docker_b.get(key)
            if va is None and vb is None:
                continue
            if _matches_ignore("docker", key, ignore_rules):
                continue
            if va is None:
                result.drifts.append(
                    DriftEntry(
                        type="docker",
                        severity=sev,
                        key=key,
                        value_a=None,
                        value_b=str(vb) if not isinstance(vb, dict) else str(vb),
                        details={"category": "docker", "reason": f"{label} added"},
                    )
                )
            elif vb is None:
                result.drifts.append(
                    DriftEntry(
                        type="docker",
                        severity=sev,
                        key=key,
                        value_a=str(va) if not isinstance(va, dict) else str(va),
                        value_b=None,
                        details={"category": "docker", "reason": f"{label} removed"},
                    )
                )
            else:
                sa = str(va) if not isinstance(va, dict) else f"{va.get('id','')} {va.get('version_id','')}".strip()
                sb = str(vb) if not isinstance(vb, dict) else f"{vb.get('id','')} {vb.get('version_id','')}".strip()
                if sa != sb:
                    result.drifts.append(
                        DriftEntry(
                            type="docker",
                            severity=sev,
                            key=key,
                            value_a=sa or str(va),
                            value_b=sb or str(vb),
                            details={"category": "docker", "reason": f"{label} changed"},
                        )
                    )

    # Kubernetes
    k8s_a = report_a.get("k8s") or {}
    k8s_b = report_b.get("k8s") or {}
    if k8s_a or k8s_b:
        _compare_k8s(k8s_a, k8s_b, result, ignore_rules)

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
