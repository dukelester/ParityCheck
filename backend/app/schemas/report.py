"""Report schemas."""

from pydantic import BaseModel


class ReportCreate(BaseModel):
    env: str
    os: dict | None = None
    runtime: dict | None = None
    deps: dict = {}
    direct_dependencies: dict | None = None
    installed_dependencies: dict | None = None
    transitive_dependencies: dict | None = None
    env_vars: dict = {}
    env_var_hashes: dict | None = None
    db_schema_hash: str | None = None
    docker: dict | None = None
    k8s: dict | None = None
    required_by: dict | None = None


class ReportResponse(BaseModel):
    id: str
    env: str
    timestamp: str
    status: str
    health_score: int | None = None
