import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from agent.config import settings

logger = logging.getLogger(__name__)

async_engine: AsyncEngine | None = None

if settings.DATABASE_BACKEND == "sqlite":
    async_engine = create_async_engine(settings.DATABASE_URL, echo=False)
elif settings.DATABASE_BACKEND == "postgres":
    async_engine = create_async_engine(
        settings.DATABASE_URL, echo=False, pool_pre_ping=True, pool_size=5, max_overflow=10
    )
else:
    raise Exception("DATABASE_BACKEND must be sqlite or postgres.")


async_session = async_sessionmaker[AsyncSession](async_engine, expire_on_commit=False)


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


async def _get_existing_columns(conn, table_name: str) -> set[str]:
    """获取表的现有列名（兼容 SQLite 和 PostgreSQL）。"""
    if settings.DATABASE_BACKEND == "sqlite":
        result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
        rows = result.fetchall()
        return {row[1] for row in rows}
    else:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :tbl"
            ),
            {"tbl": table_name},
        )
        rows = result.fetchall()
        return {row[0] for row in rows}


async def _table_exists(conn, table_name: str) -> bool:
    """Check if a table exists (SQLite / PostgreSQL compatible)."""
    if settings.DATABASE_BACKEND == "sqlite":
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
            {"name": table_name},
        )
        return result.scalar() is not None
    else:
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = :name)"
            ),
            {"name": table_name},
        )
        return result.scalar()


async def _migrate_personnel_user_id_to_account_id(conn):
    """Rename personnel.user_id column to account_id and update FK."""
    if not await _table_exists(conn, "personnel"):
        return

    cols = await _get_existing_columns(conn, "personnel")
    if "account_id" in cols and "user_id" not in cols:
        return  # already migrated

    if "user_id" not in cols:
        return  # no old column to rename

    logger.info("重命名 personnel.user_id → account_id ...")
    is_pg = settings.DATABASE_BACKEND == "postgres"

    if is_pg:
        await conn.execute(
            text("ALTER TABLE personnel DROP CONSTRAINT IF EXISTS personnel_user_id_fkey")
        )
        await conn.execute(
            text("ALTER TABLE personnel RENAME COLUMN user_id TO account_id")
        )
        await conn.execute(
            text(
                "ALTER TABLE personnel ADD CONSTRAINT personnel_account_id_fkey "
                "FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL"
            )
        )
    else:
        # SQLite: rebuild table
        await conn.execute(text("ALTER TABLE personnel RENAME COLUMN user_id TO account_id"))


async def _migrate_users_to_accounts(conn):
    """Migrate data from old users table to accounts table, then drop users."""
    if not await _table_exists(conn, "users"):
        return

    # Check if accounts already has data
    result = await conn.execute(text("SELECT count(*) FROM accounts"))
    if result.scalar() > 0:
        logger.info("accounts 表已有数据，跳过 users 迁移")
        return

    logger.info("正在将 users 表数据迁移到 accounts 表...")
    result = await conn.execute(text("SELECT * FROM users"))
    rows = result.fetchall()

    if rows:
        # Copy each row
        for row in rows:
            row_dict = dict(row._mapping)
            await conn.execute(
                text(
                    "INSERT INTO accounts (id, username, nickname, password_hash, "
                    "phone, email, avatar, workspace_id, is_active, created_at, updated_at) "
                    "VALUES (:id, :username, :nickname, :password_hash, :phone, :email, "
                    ":avatar, :workspace_id, :is_active, :created_at, :updated_at)"
                ),
                row_dict,
            )

    # Drop old FK constraints referencing users
    is_pg = settings.DATABASE_BACKEND == "postgres"
    if is_pg:
        # PostgreSQL: drop constraints by name
        for tbl, fk_name in [
            ("user_oauths", "user_oauths_user_id_fkey"),
            ("personnel", "personnel_account_id_fkey"),
        ]:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {fk_name}")
                )
            except Exception:
                pass
    else:
        # SQLite: recreate tables without old FKs (handled by DROP CASCADE-like rebuild)
        pass

    # Drop old users table (CASCADE for PostgreSQL to handle remaining dependencies)
    if is_pg:
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        # Recreate FK constraints pointing to accounts instead of users
        for tbl, fk_name, ref_table in [
            ("user_oauths", "user_oauths_user_id_fkey", "accounts"),
            ("personnel", "personnel_account_id_fkey", "accounts"),
        ]:
            try:
                await conn.execute(
                    text(
                        f"ALTER TABLE {tbl} ADD CONSTRAINT {fk_name} "
                        f"FOREIGN KEY ({'account_id' if 'personnel' in tbl else 'user_id'}) "
                        f"REFERENCES {ref_table}(id) "
                        f"ON DELETE SET NULL"
                    )
                )
            except Exception:
                pass
    else:
        await conn.execute(text("DROP TABLE IF EXISTS users"))

    logger.info(
        f"已迁移 {len(rows)} 条记录到 accounts 表，并删除 users 表"
        if rows else "users 表无数据，已删除"
    )


async def init_db():
    from db.base import Base
    from db.models.cron_job import CronJob  # noqa: F401  ensure table is registered

    # 断言 async_engine 不为 None，类型检查器会据此收窄类型
    assert async_engine is not None, "数据库引擎没有被初始化"

    logger.info("初始化数据库...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_personnel_user_id_to_account_id(conn)
        await _migrate_users_to_accounts(conn)

    logger.info("数据库表已创建")
