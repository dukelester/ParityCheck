"""Report schemas."""

from pydantic import BaseModel


class ReportCreate(BaseModel):
    env: str
    os: dict | None = None
    runtime: dict | None = None
    deps: dict = {}
    env_vars: dict = {}
    db_schema_hash: str | None = None


class ReportResponse(BaseModel):
    id: str
    env: str
    timestamp: str
    status: str
