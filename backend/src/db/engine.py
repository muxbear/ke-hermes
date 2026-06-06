import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from agent.config import settings

logger = logging.getLogger(__name__)

async_engine = None
if settings.DATABASE_BACKEND == "sqlite":
    async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
elif settings.DATABASE_BACKEND == "postgres":
    async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
else:
    raise Exception("DATABASE_BACKEND must be sqlite or postgres.")

async_session = async_sessionmaker(async_engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    from db.base import Base

    logger.info("Initializing database...")
    async with async_engine.begin() as conn:
        await _migrate_agents_drop_user_id(conn)
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")


async def _migrate_agents_drop_user_id(conn) -> None:
    """Remove the user_id column from agents table if it exists."""
    from sqlalchemy import inspect, text

    tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if "agents" not in tables:
        return

    columns = await conn.run_sync(
        lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("agents")]
    )
    if "user_id" not in columns:
        return

    logger.info("Migrating: removing user_id column from agents table")
    if settings.DATABASE_BACKEND == "postgres":
        await conn.execute(text("ALTER TABLE agents DROP COLUMN IF EXISTS user_id"))
    else:
        # SQLite: recreate table (drop FK table first to avoid constraint errors)
        await conn.execute(text("DROP TABLE IF EXISTS agent_files"))
        await conn.execute(text("DROP TABLE IF EXISTS agents"))
