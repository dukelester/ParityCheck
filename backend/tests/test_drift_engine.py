"""Unit tests for drift engine."""

import pytest

from app.services.drift_engine import (
    CRITICAL_FLOOR,
    MAX_TOTAL_DEDUCTION,
    SEVERITY_WEIGHTS,
    SYSTEM_PACKAGES,
    compare_reports,
)


def test_direct_dependency_missing_high():
    """Direct dependency missing in target → severity = high."""
    baseline = {
        "direct_dependencies": {"Django": "4.2.5", "requests": "2.31.0"},
        "installed_dependencies": {"Django": "4.2.5", "requests": "2.31.0", "urllib3": "2.1.0"},
        "transitive_dependencies": {"urllib3": "2.1.0"},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {"requests": "2.31.0"},
        "installed_dependencies": {"requests": "2.31.0", "urllib3": "2.1.0"},
        "transitive_dependencies": {"urllib3": "2.1.0"},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    drifts = [d for d in result.drifts if d.type == "dependency" and d.key == "Django"]
    assert len(drifts) == 1
    assert drifts[0].severity == "high"
    assert drifts[0].details.get("reason") == "Missing direct dependency"


def test_transitive_dependency_missing_low():
    """Transitive dependency missing → severity = low."""
    baseline = {
        "direct_dependencies": {"Django": "4.2.5"},
        "installed_dependencies": {"Django": "4.2.5", "urllib3": "2.1.0"},
        "transitive_dependencies": {"urllib3": "2.1.0"},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {"Django": "4.2.5"},
        "installed_dependencies": {"Django": "4.2.5"},
        "transitive_dependencies": {},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    drifts = [d for d in result.drifts if d.type == "dependency" and d.key == "urllib3"]
    assert len(drifts) == 1
    assert drifts[0].severity == "low"
    assert "transitive" in drifts[0].details.get("category", "")


def test_major_version_mismatch_high():
    """Major version mismatch → high."""
    baseline = {
        "direct_dependencies": {"Django": "4.2.5"},
        "installed_dependencies": {"Django": "4.2.5"},
        "transitive_dependencies": {},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {"Django": "3.2.19"},
        "installed_dependencies": {"Django": "3.2.19"},
        "transitive_dependencies": {},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    drifts = [d for d in result.drifts if d.type == "dependency" and d.key == "Django"]
    assert len(drifts) == 1
    assert drifts[0].severity == "high"
    assert drifts[0].value_a == "4.2.5"
    assert drifts[0].value_b == "3.2.19"


def test_patch_mismatch_low():
    """Patch version mismatch → low."""
    baseline = {
        "direct_dependencies": {"requests": "2.31.0"},
        "installed_dependencies": {"requests": "2.31.0", "urllib3": "2.1.0"},
        "transitive_dependencies": {"urllib3": "2.1.0"},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {"requests": "2.31.0"},
        "installed_dependencies": {"requests": "2.31.0", "urllib3": "2.1.1"},
        "transitive_dependencies": {"urllib3": "2.1.1"},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    drifts = [d for d in result.drifts if d.type == "dependency" and d.key == "urllib3"]
    assert len(drifts) == 1
    assert drifts[0].severity == "low"


def test_system_package_ignored():
    """System packages (pip, setuptools, wheel) → ignored."""
    baseline = {
        "direct_dependencies": {},
        "installed_dependencies": {"pip": "24.0", "setuptools": "69.0", "Django": "4.2.5"},
        "transitive_dependencies": {"Django": "4.2.5"},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {},
        "installed_dependencies": {"pip": "23.0", "setuptools": "68.0", "Django": "4.2.5"},
        "transitive_dependencies": {"Django": "4.2.5"},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    dep_drifts = [d for d in result.drifts if d.type == "dependency"]
    system_drifts = [d for d in dep_drifts if d.key in SYSTEM_PACKAGES]
    assert len(system_drifts) == 0


def test_health_score_cap():
    """Health score never collapses below 10 (unless critical); cap at 90 deduction."""
    baseline = {
        "direct_dependencies": {f"pkg{i}": "1.0.0" for i in range(10)},
        "installed_dependencies": {f"pkg{i}": "1.0.0" for i in range(10)},
        "transitive_dependencies": {},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {},
        "installed_dependencies": {},
        "transitive_dependencies": {},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    # 10 high drifts = 10 * 20 = 200, capped at 90
    assert result.health_score == 100 - MAX_TOTAL_DEDUCTION
    assert result.health_score >= 10


def test_critical_floor():
    """If any critical drift exists, score capped at CRITICAL_FLOOR."""
    baseline = {"deps": {}, "env_vars": {"DATABASE_URL": "postgres://..."}}
    target = {"deps": {}, "env_vars": {}}
    result = compare_reports(baseline, target)
    assert any(d.severity == "critical" for d in result.drifts)
    assert result.health_score <= CRITICAL_FLOOR


def test_summary_breakdown():
    """Summary includes critical/high/medium/low counts."""
    baseline = {
        "direct_dependencies": {"Django": "4.2.5", "requests": "2.31.0"},
        "installed_dependencies": {"Django": "4.2.5", "requests": "2.31.0", "urllib3": "2.1.0"},
        "transitive_dependencies": {"urllib3": "2.1.0"},
        "deps": {},
        "env_vars": {},
    }
    target = {
        "direct_dependencies": {"Django": "3.2.19", "requests": "2.30.0", "urllib3": "2.1.1"},
        "installed_dependencies": {"Django": "3.2.19", "requests": "2.30.0", "urllib3": "2.1.1"},
        "transitive_dependencies": {"urllib3": "2.1.1"},
        "deps": {},
        "env_vars": {},
    }
    result = compare_reports(baseline, target)
    assert "summary" in result.to_dict()
    s = result.summary
    assert "critical" in s
    assert "high" in s
    assert "medium" in s
    assert "low" in s


def test_legacy_flat_deps():
    """Legacy flat deps format still works."""
    baseline = {"deps": {"Django": "4.2.5"}, "env_vars": {}}
    target = {"deps": {"Django": "3.2.19"}, "env_vars": {}}
    result = compare_reports(baseline, target)
    drifts = [d for d in result.drifts if d.type == "dependency"]
    assert len(drifts) >= 1
    assert drifts[0].key == "Django"
    assert drifts[0].details.get("category") == "legacy"
