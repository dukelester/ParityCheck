"""SQLAlchemy models for ParityCheck production platform."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    verification_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    password_reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    password_reset_token_expires: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    api_keys = relationship("ApiKey", back_populates="user")
    owned_workspaces = relationship("Workspace", back_populates="owner", foreign_keys="Workspace.owner_id")
    workspace_memberships = relationship("WorkspaceMember", back_populates="user")
    environments = relationship("Environment", back_populates="user", foreign_keys="Environment.user_id")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workspace_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True
    )  # null = default workspace
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="api_keys")
    workspace = relationship("Workspace", back_populates="api_keys")


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")  # free, pro, enterprise
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="owned_workspaces", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace")
    environments = relationship("Environment", back_populates="workspace")
    ignore_rules = relationship("IgnoreRule", back_populates="workspace")
    alerts = relationship("Alert", back_populates="workspace")
    api_keys = relationship("ApiKey", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # owner, admin, member
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspace_memberships")

    __table_args__ = (Index("ix_workspace_member_ws_user", "workspace_id", "user_id", unique=True),)


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=True
    )  # null during migration
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )  # legacy, for migration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # dev, staging, prod
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="environments", foreign_keys=[workspace_id])
    user = relationship("User", back_populates="environments", foreign_keys=[user_id])
    reports = relationship("Report", back_populates="environment")

    __table_args__ = (Index("ix_env_workspace_name", "workspace_id", "name", unique=True),)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    env_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("environments.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    os: Mapped[dict] = mapped_column(JSON, nullable=True)
    python_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    deps: Mapped[dict] = mapped_column(JSON, default=dict)
    env_vars: Mapped[dict] = mapped_column(JSON, default=dict)
    db_schema_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    health_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0-100

    environment = relationship("Environment", back_populates="reports")
    drifts = relationship("Drift", back_populates="report")


class Drift(Base):
    __tablename__ = "drifts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # runtime, dependency, env_var, db_schema
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # critical, high, medium, low
    key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    value_a: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_b: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="drifts")


class IgnoreRule(Base):
    __tablename__ = "ignore_rules"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # env_var, dependency, runtime
    key_pattern: Mapped[str] = mapped_column(String(255), nullable=False)  # exact, wildcard (*), regex
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="ignore_rules")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # slack, email, webhook
    config: Mapped[dict] = mapped_column(JSON, nullable=False)  # encrypted webhook_url etc
    min_severity: Mapped[str] = mapped_column(String(20), default="high")  # critical, high, medium, low
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="alerts")


class Billing(Base):
    __tablename__ = "billing"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    status: Mapped[str] = mapped_column(String(20), default="active")
    stripe_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
