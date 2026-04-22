from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models import Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_task_columns(conn)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def _ensure_task_columns(conn) -> None:
    """
    Lightweight SQLite migration for iterative MVP development.
    Keeps existing local data usable when new ORM columns are added.
    """
    if conn.dialect.name != "sqlite":
        return

    table_info = await conn.execute(text("PRAGMA table_info(tasks)"))
    existing_columns = {row[1] for row in table_info.fetchall()}

    if "category_weight" not in existing_columns:
        await conn.execute(
            text("ALTER TABLE tasks ADD COLUMN category_weight FLOAT NOT NULL DEFAULT 1.0")
        )
    if "actual_time_taken" not in existing_columns:
        await conn.execute(
            text("ALTER TABLE tasks ADD COLUMN actual_time_taken INTEGER")
        )
