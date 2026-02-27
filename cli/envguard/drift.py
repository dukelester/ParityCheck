"""Local drift comparison (mirrors backend drift_engine)."""

from dataclasses import dataclass, field

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


def _check_security_cli(report: dict, result: DriftResult) -> None:
    """Weak config, DEBUG in prod, AWS S3 advisory."""
    ev = report.get("env_vars") or {}
    env_name = (report.get("env") or "").lower()

    if "prod" in env_name or "production" in env_name:
        debug_val = ev.get("DEBUG", ev.get("DJANGO_DEBUG", "")).lower()
        if debug_val in ("true", "1", "yes"):
            result.drifts.append(
                DriftEntry(
                    "config", "critical", "DEBUG", None, "True",
                    {"category": "security", "reason": "DEBUG enabled in production"},
                )
            )

    for key in ev:
        if "secret" in key.lower() or key in ("SECRET_KEY", "DJANGO_SECRET_KEY"):
            v = str(ev.get(key, "")).lower()
            if v and "redacted" not in v:
                for weak in WEAK_SECRET_VALUES:
                    if weak in v or v == weak:
                        result.drifts.append(
                            DriftEntry(
                                "config", "high", key, None, "***",
                                {"category": "weak_config", "reason": "Weak secret value"},
                            )
                        )
                        break

    if ev.get("AWS_ACCESS_KEY_ID") or ev.get("AWS_SECRET_ACCESS_KEY"):
        result.drifts.append(
            DriftEntry(
                "config", "medium", "AWS_CREDENTIALS", None, "present",
                {"category": "security", "reason": "AWS creds - audit S3 public access"},
            )
        )


def _compare_k8s_cli(k8s_a: dict, k8s_b: dict, result: DriftResult) -> None:
    """Compare K8s deployments, configmaps, secrets."""
    def _add(sev: str, key: str, va, vb, reason: str) -> None:
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

    cm_a = k8s_a.get("configmaps") or {}
    cm_b = k8s_b.get("configmaps") or {}
    for name in set(cm_a) | set(cm_b):
        ha = (cm_a.get(name) or {}).get("data_hash")
        hb = (cm_b.get(name) or {}).get("data_hash")
        if ha is None:
            _add("high", f"configmap:{name}", None, hb, "ConfigMap added")
        elif hb is None:
            _add("high", f"configmap:{name}", ha, None, "ConfigMap removed")
        elif ha != hb:
            _add("high", f"configmap:{name}", ha, hb, "ConfigMap data changed")

    sec_a = k8s_a.get("secrets") or {}
    sec_b = k8s_b.get("secrets") or {}
    for name in set(sec_a) | set(sec_b):
        ha = (sec_a.get(name) or {}).get("data_hash")
        hb = (sec_b.get(name) or {}).get("data_hash")
        if ha is None:
            _add("critical", f"secret:{name}", None, hb, "Secret added")
        elif hb is None:
            _add("critical", f"secret:{name}", ha, None, "Secret removed")
        elif ha != hb:
            _add("critical", f"secret:{name}", ha, hb, "Secret data changed")

    dep_a = k8s_a.get("deployments") or {}
    dep_b = k8s_b.get("deployments") or {}
    for name in set(dep_a) | set(dep_b):
        da, db = dep_a.get(name) or {}, dep_b.get(name) or {}
        if not da:
            _add("high", f"deployment:{name}", None, "present", "Deployment added")
            continue
        if not db:
            _add("high", f"deployment:{name}", "present", None, "Deployment removed")
            continue

        ra, rb = da.get("replicas"), db.get("replicas")
        if ra is not None and rb is not None and ra != rb:
            _add("medium", f"deployment:{name}.replicas", ra, rb, "Replica count changed")

        ca_list = da.get("containers") or []
        cb_list = db.get("containers") or []
        cb_by_name = {c.get("name"): c for c in cb_list if c.get("name")}
        for ca in ca_list:
            cname = ca.get("name", "")
            cb = cb_by_name.get(cname) if cname else (cb_list[0] if cb_list else {})
            prefix = f"deployment:{name}.{cname}" if cname else f"deployment:{name}"

            img_a, img_b = ca.get("image"), cb.get("image") if cb else None
            if img_a and img_b and img_a != img_b:
                _add("high", f"{prefix}.image", img_a, img_b, "Image tag changed")

            res_a = ca.get("resources") or {}
            res_b = cb.get("resources") or {} if cb else {}
            limits_a, limits_b = res_a.get("limits") or {}, res_b.get("limits") or {}
            if limits_a != limits_b:
                _add("medium", f"{prefix}.limits", str(limits_a), str(limits_b), "Resource limits changed")

            ev_a = ca.get("env_vars") or {}
            ev_b = cb.get("env_vars") or {} if cb else {}
            for k in set(ev_a) | set(ev_b):
                va, vb = ev_a.get(k), ev_b.get(k)
                if va != vb:
                    _add("medium", f"{prefix}.env.{k}", va, vb, "Env var changed")


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
    hash_a = report_a.get("env_var_hashes") or {}
    hash_b = report_b.get("env_var_hashes") or {}
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
        elif _is_sensitive_key(k) and hash_a.get(k) and hash_b.get(k):
            if hash_a.get(k) != hash_b.get(k):
                result.drifts.append(
                    DriftEntry(
                        "secret_drift", "critical", k, "***", "***",
                        {"change": "value", "reason": "Secret value changed"},
                    )
                )
        elif str(va) != str(vb):
            result.drifts.append(
                DriftEntry("environment_variable", "medium", k, str(va), str(vb))
            )

    _check_security_cli(report_b, result)

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
            if va is None:
                vstr = str(vb) if not isinstance(vb, dict) else str(vb)
                result.drifts.append(
                    DriftEntry("docker", sev, key, None, vstr, {"category": "docker", "reason": f"{label} added"})
                )
            elif vb is None:
                vstr = str(va) if not isinstance(va, dict) else str(va)
                result.drifts.append(
                    DriftEntry("docker", sev, key, vstr, None, {"category": "docker", "reason": f"{label} removed"})
                )
            else:
                sa = str(va) if not isinstance(va, dict) else f"{va.get('id','')} {va.get('version_id','')}".strip()
                sb = str(vb) if not isinstance(vb, dict) else f"{vb.get('id','')} {vb.get('version_id','')}".strip()
                if sa != sb:
                    result.drifts.append(
                        DriftEntry("docker", sev, key, sa or str(va), sb or str(vb), {"category": "docker", "reason": f"{label} changed"})
                    )

    # Kubernetes
    k8s_a = report_a.get("k8s") or {}
    k8s_b = report_b.get("k8s") or {}
    if k8s_a or k8s_b:
        _compare_k8s_cli(k8s_a, k8s_b, result)

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
