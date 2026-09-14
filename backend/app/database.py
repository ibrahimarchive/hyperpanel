"""
Database engine and session management.
Uses SQLAlchemy async with aiosqlite.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


from sqlalchemy import text

async def init_db():
    """Create all tables on startup and apply missing column migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Automatic column migrations for SQLite
        try:
            columns_res = await conn.execute(text("PRAGMA table_info(users);"))
            existing_columns = {row[1] for row in columns_res.fetchall()}

            if existing_columns:
                if "totp_secret" not in existing_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN totp_secret VARCHAR(64) DEFAULT NULL;"))
                if "totp_enabled" not in existing_columns:
                    await conn.execute(text("ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN DEFAULT 0 NOT NULL;"))
        except Exception:
            pass
