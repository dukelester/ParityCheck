"""End-to-end CLI tests: collect, compare, report flow."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from envguard.main import app

runner = CliRunner()
CACHE_DIR = Path.home() / ".envguard"


E2E_ENVS = ("e2e_dev", "e2e_prod", "e2e_staging", "e2e_nonexistent")


def _clean_cache():
    """Remove test cache files only (e2e_* envs)."""
    for env in E2E_ENVS:
        p = CACHE_DIR / f"report_{env}.json"
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass


@pytest.fixture(autouse=True)
def clean_cache():
    """Clean cache before/after each test."""
    _clean_cache()
    yield
    _clean_cache()


def test_e2e_collect_compare_flow():
    """Collect dev, collect prod, compare -> shows drift summary."""
    r1 = runner.invoke(app, ["collect", "--env=e2e_dev"])
    assert r1.exit_code == 0

    r2 = runner.invoke(app, ["collect", "--env=e2e_prod"])
    assert r2.exit_code == 0

    r3 = runner.invoke(app, ["compare", "--env=e2e_prod", "--baseline=e2e_dev"])
    assert r3.exit_code == 0
    assert "Drift" in r3.output or "deps" in r3.output or "env_vars" in r3.output


def test_e2e_collect_produces_valid_report():
    """Collect produces JSON with required fields."""
    out_path = CACHE_DIR / "report_e2e_dev.json"
    runner.invoke(app, ["collect", "--env=e2e-dev", "-o", str(out_path)])
    assert out_path.exists()
    data = json.loads(out_path.read_text())
    assert data["env"] == "e2e-dev"
    assert "os" in data
    assert "runtime" in data
    assert "deps" in data
    assert "env_vars" in data
    assert "direct_dependencies" in data
    assert "installed_dependencies" in data


def test_e2e_compare_requires_both_reports():
    """Compare fails when baseline or current report missing."""
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / "report_e2e_dev.json").write_text(
        json.dumps({"env": "e2e_dev", "deps": {}, "env_vars": {}})
    )
    r = runner.invoke(app, ["compare", "--env=e2e_nonexistent", "--baseline=e2e_dev"])
    assert r.exit_code != 0
    assert "No report found" in r.output or "e2e_nonexistent" in r.output.lower()


def test_e2e_report_requires_collect_first():
    """Report fails when no cached report."""
    r = runner.invoke(app, ["report", "--api-key=pc_test", "--env=e2e_nonexistent"])
    assert r.exit_code != 0
    assert "No report found" in r.output or "collect" in r.output.lower()


@patch("envguard.commands.report.httpx.Client")
def test_e2e_report_upload_mock(mock_client_cls):
    """Report uploads to API when report exists (mocked)."""
    CACHE_DIR.mkdir(exist_ok=True)
    report_path = CACHE_DIR / "report_e2e_dev.json"
    report_path.write_text(
        json.dumps({
            "env": "e2e_dev",
            "os": {"system": "Linux"},
            "runtime": {"python_version": "3.12"},
            "deps": {},
            "env_vars": {},
        })
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__enter__.return_value = mock_client
    mock_client_cls.return_value.__exit__.return_value = False

    r = runner.invoke(app, ["report", "--api-key=pc_test123", "--env=e2e_dev"])
    assert r.exit_code == 0
    assert "uploaded" in r.output.lower() or "success" in r.output.lower()
    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "api/v1/reports" in str(call_args[0][0])
    assert call_args[1]["headers"]["X-API-Key"] == "pc_test123"


def test_e2e_check_help():
    """Check command has expected options."""
    r = runner.invoke(app, ["check", "--help"])
    assert r.exit_code == 0
    assert "api-key" in r.output
    assert "fail-on-drift" in r.output or "fail_on_drift" in r.output


def test_e2e_history_lists_cached():
    """History lists cached reports."""
    CACHE_DIR.mkdir(exist_ok=True)
    (CACHE_DIR / "report_e2e_dev.json").write_text(json.dumps({"env": "e2e_dev"}))
    (CACHE_DIR / "report_e2e_prod.json").write_text(json.dumps({"env": "e2e_prod"}))
    r = runner.invoke(app, ["history"])
    assert r.exit_code == 0
    assert "e2e_dev" in r.output or "e2e_prod" in r.output or "report" in r.output.lower()
