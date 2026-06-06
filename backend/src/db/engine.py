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
        await _migrate_agents_drop_skills(conn)
        await _migrate_skills_drop_user_id(conn)
        await _migrate_agents_drop_tools_column(conn)
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_agents_add_provider_model(conn)
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


async def _migrate_agents_drop_skills(conn) -> None:
    """Remove the skills JSON column from agents table if it exists."""
    from sqlalchemy import inspect, text

    tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if "agents" not in tables:
        return

    columns = await conn.run_sync(
        lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("agents")]
    )
    if "skills" not in columns:
        return

    logger.info("Migrating: removing skills column from agents table")
    if settings.DATABASE_BACKEND == "postgres":
        await conn.execute(text("ALTER TABLE agents DROP COLUMN IF EXISTS skills"))
    else:
        # SQLite: drop agent_skills and recreate agents (FK constraint)
        await conn.execute(text("DROP TABLE IF EXISTS agent_skills"))
        await conn.execute(text("DROP TABLE IF EXISTS agent_files"))
        await conn.execute(text("DROP TABLE IF EXISTS agents"))


async def _migrate_skills_drop_user_id(conn) -> None:
    """Remove the user_id column from skills table if it exists."""
    from sqlalchemy import inspect, text

    tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if "skills" not in tables:
        return

    columns = await conn.run_sync(
        lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("skills")]
    )
    if "user_id" not in columns:
        return

    logger.info("Migrating: removing user_id column from skills table")
    if settings.DATABASE_BACKEND == "postgres":
        await conn.execute(text("ALTER TABLE skills DROP COLUMN IF EXISTS user_id"))
    else:
        # SQLite: drop agent_skills and recreate skills (FK constraint)
        await conn.execute(text("DROP TABLE IF EXISTS agent_skills"))
        await conn.execute(text("DROP TABLE IF EXISTS skills"))


async def _migrate_agents_add_provider_model(conn) -> None:
    """Add provider_id and model_id columns to agents table if they don't exist."""
    from sqlalchemy import inspect, text

    tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if "agents" not in tables:
        return

    columns = await conn.run_sync(
        lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("agents")]
    )

    if "provider_id" not in columns:
        logger.info("Migrating: adding provider_id column to agents table")
        await conn.execute(text("ALTER TABLE agents ADD COLUMN provider_id VARCHAR(36)"))

    if "model_id" not in columns:
        logger.info("Migrating: adding model_id column to agents table")
        await conn.execute(text("ALTER TABLE agents ADD COLUMN model_id VARCHAR(36)"))


async def _migrate_agents_drop_tools_column(conn) -> None:
    """Remove the tools JSON column from agents table if it exists."""
    from sqlalchemy import inspect, text

    tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    if "agents" not in tables:
        return

    columns = await conn.run_sync(
        lambda sync_conn: [c["name"] for c in inspect(sync_conn).get_columns("agents")]
    )
    if "tools" not in columns:
        return

    logger.info("Migrating: removing tools column from agents table")
    if settings.DATABASE_BACKEND == "postgres":
        await conn.execute(text("ALTER TABLE agents DROP COLUMN IF EXISTS tools"))
    else:
        # SQLite: drop dependent tables and recreate agents
        await conn.execute(text("DROP TABLE IF EXISTS agent_tools"))
        await conn.execute(text("DROP TABLE IF EXISTS agent_files"))
        await conn.execute(text("DROP TABLE IF EXISTS agents"))
