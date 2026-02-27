"""Database session management."""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)

_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://") and "asyncpg" not in _db_url:
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_db_url, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def _migrate_users_table(conn) -> None:
    """Add github_id and make hashed_password nullable if columns are missing (PostgreSQL)."""
    try:
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'github_id'
            """)
        )
        if result.scalar() is None:
            logger.info("Adding github_id column to users table")
            await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS github_id VARCHAR(64) UNIQUE"))
        result = await conn.execute(
            text("""
                SELECT is_nullable FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'hashed_password'
            """)
        )
        row = result.fetchone()
        if row and row[0] == "NO":
            logger.info("Making hashed_password nullable in users table")
            await conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"))
        # Password reset columns
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'password_reset_token'
            """)
        )
        if result.scalar() is None:
            logger.info("Adding password_reset_token columns to users table")
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token VARCHAR(128)")
            )
            await conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token)")
            )
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token_expires TIMESTAMP")
            )
    except Exception as e:
        logger.warning("Migration skipped (may not be PostgreSQL or table missing): %s", e)


async def _migrate_workspaces(conn) -> None:
    """Add workspace columns and migrate existing environments."""
    try:
        # Add workspace_id, user_id, is_baseline to environments
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'environments' AND column_name = 'workspace_id'
            """)
        )
        if result.scalar() is None:
            logger.info("Adding workspace_id to environments")
            await conn.execute(
                text("ALTER TABLE environments ADD COLUMN IF NOT EXISTS workspace_id UUID")
            )
            await conn.execute(
                text("ALTER TABLE environments ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id)")
            )
            await conn.execute(
                text("ALTER TABLE environments ADD COLUMN IF NOT EXISTS is_baseline BOOLEAN DEFAULT FALSE")
            )
        # Ensure user_id is nullable (workspace-owned envs have user_id=NULL)
        try:
            await conn.execute(
                text("ALTER TABLE environments ALTER COLUMN user_id DROP NOT NULL")
            )
        except Exception:
            pass  # Column may already be nullable
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'reports' AND column_name = 'health_score'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS health_score INTEGER")
            )
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'reports' AND column_name = 'docker'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS docker JSON")
            )
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'reports' AND column_name = 'k8s'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS k8s JSON")
            )
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'reports' AND column_name = 'env_var_hashes'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE reports ADD COLUMN IF NOT EXISTS env_var_hashes JSON")
            )
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'drifts' AND column_name = 'severity'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE drifts ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'medium'")
            )
            await conn.execute(
                text("ALTER TABLE drifts ADD COLUMN IF NOT EXISTS key VARCHAR(255)")
            )
            await conn.execute(
                text("ALTER TABLE drifts ADD COLUMN IF NOT EXISTS value_a TEXT")
            )
            await conn.execute(
                text("ALTER TABLE drifts ADD COLUMN IF NOT EXISTS value_b TEXT")
            )
        result = await conn.execute(
            text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'api_keys' AND column_name = 'workspace_id'
            """)
        )
        if result.scalar() is None:
            await conn.execute(
                text("ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS workspace_id UUID")
            )
    except Exception as e:
        logger.warning("Workspace migration skipped: %s", e)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await _migrate_users_table(conn)
    async with engine.begin() as conn:
        await _migrate_workspaces(conn)
