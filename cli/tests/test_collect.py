"""Tests for collect command."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from envguard.main import app

runner = CliRunner()


def test_collect_help():
    result = runner.invoke(app, ["collect", "--help"])
    assert result.exit_code == 0
    assert "Collect" in result.output


def test_collect_default():
    result = runner.invoke(app, ["collect", "--env=dev"])
    assert result.exit_code == 0
    assert "dev" in result.output
    cache = Path.home() / ".envguard" / "report_dev.json"
    assert cache.exists()
    data = json.loads(cache.read_text())
    assert data["env"] == "dev"
    assert "os" in data
    assert "runtime" in data
    assert "deps" in data
    assert "env_vars" in data
    assert "direct_dependencies" in data
    assert "installed_dependencies" in data
    assert "transitive_dependencies" in data
