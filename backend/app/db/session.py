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
    except Exception as e:
        logger.warning("Migration skipped (may not be PostgreSQL or table missing): %s", e)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await _migrate_users_table(conn)
