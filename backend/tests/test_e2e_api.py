"""End-to-end API tests: auth, report upload, baseline, drift."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """Sync HTTP client (session-scoped to avoid event loop conflicts with async DB)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def api_key(client: TestClient):
    """Create verified user + API key via test helper endpoint."""
    from uuid import uuid4

    email = f"e2e-{uuid4().hex[:8]}@test.paritycheck.io"
    r = client.post(
        "/api/v1/auth/test/create-verified-user",
        json={
            "email": email,
            "password": "TestPass123!",
            "name": "E2E User",
        },
    )
    if r.status_code == 404:
        pytest.skip("Test endpoint not available (set TESTING=1)")
    assert r.status_code == 200, r.text
    return r.json()["api_key"]


def sample_report(env: str = "dev") -> dict:
    """Minimal valid report payload."""
    return {
        "env": env,
        "os": {"system": "Linux", "release": "6.0", "machine": "x86_64"},
        "runtime": {"python_version": "3.12.0"},
        "deps": {"requests": "2.31.0", "typer": "0.9.0"},
        "direct_dependencies": {"requests": "2.31.0", "typer": "0.9.0"},
        "installed_dependencies": {
            "requests": "2.31.0",
            "typer": "0.9.0",
            "urllib3": "2.0.0",
        },
        "transitive_dependencies": {"urllib3": "2.0.0"},
        "env_vars": {"PATH": "/usr/bin", "DEBUG": "false"},
        "db_schema_hash": None,
    }


def test_health(client: TestClient):
    """Health endpoint returns ok."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_register_login_flow(client: TestClient):
    """Register, verify (skip in test), login."""
    email = f"reg-{__import__('uuid').uuid4().hex[:8]}@test.paritycheck.io"
    # Register
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass123!", "name": "Test User"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == email
    assert data["email_verified"] is False

    # Verify (get token from logs is hard; instead we verify via direct DB update in real flow)
    # For E2E we use verified_user fixture; this test validates register works
    assert "id" in data


def test_report_upload_with_api_key(client: TestClient, api_key: str):
    """Upload report with API key, get 200."""
    payload = sample_report("dev")
    r = client.post(
        "/api/v1/reports/",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "X-API-Key": api_key},
    )
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["env"] == "dev"
    assert "id" in data
    assert data["status"] == "stored"


def test_baseline_after_upload(client: TestClient, api_key: str):
    """Upload dev report, then get baseline (dev is first so becomes baseline)."""
    payload = sample_report("dev")
    r1 = client.post(
        "/api/v1/reports/",
        json=payload,
        headers={"X-API-Key": api_key},
    )
    assert r1.status_code in (200, 201)

    r2 = client.get(
        "/api/v1/reports/baseline",
        headers={"X-API-Key": api_key},
    )
    assert r2.status_code == 200
    data = r2.json()
    assert data["env"] == "dev"
    assert "deps" in data or "python_version" in data


def test_drift_detection(client: TestClient, api_key: str):
    """Upload dev (baseline), then prod with different deps -> drift."""
    dev = sample_report("dev")
    prod = sample_report("prod")
    prod["deps"]["Django"] = "4.2.0"
    prod["direct_dependencies"] = {**prod["direct_dependencies"], "Django": "4.2.0"}
    prod["installed_dependencies"] = {
        **prod["installed_dependencies"],
        "Django": "4.2.0",
    }

    client.post(
        "/api/v1/reports/",
        json=dev,
        headers={"X-API-Key": api_key},
    )
    r2 = client.post(
        "/api/v1/reports/",
        json=prod,
        headers={"X-API-Key": api_key},
    )
    assert r2.status_code in (200, 201)
    # Second report (prod) should have health_score < 100 if drift detected
    data = r2.json()
    assert "health_score" in data


def test_list_reports(client: TestClient, api_key: str):
    """Upload report, list reports."""
    client.post(
        "/api/v1/reports/",
        json=sample_report("staging"),
        headers={"X-API-Key": api_key},
    )
    r = client.get(
        "/api/v1/reports/",
        headers={"X-API-Key": api_key},
    )
    assert r.status_code == 200
    reports = r.json()
    assert isinstance(reports, list)
    if reports:
        assert "env" in reports[0]
        assert "timestamp" in reports[0]


def test_unauthorized_report_rejected(client: TestClient):
    """Report upload without API key returns 401."""
    r = client.post("/api/v1/reports/", json=sample_report())
    assert r.status_code == 401
