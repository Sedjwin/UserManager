from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def migrate_db():
    """Add columns introduced after initial schema creation (idempotent)."""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE users ADD COLUMN principal_type TEXT NOT NULL DEFAULT 'human'",
        "ALTER TABLE users ADD COLUMN api_key TEXT",
    ]
    async with engine.begin() as conn:
        for stmt in stmts:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass  # column already exists


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
