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


async def _migrate_table_columns(
    conn, table_name: str, new_columns: dict[str, str]
) -> None:
    """为表添加缺失的列（如已存在则跳过），兼容 SQLite 和 PostgreSQL。"""
    existing_cols = await _get_existing_columns(conn, table_name)

    for col_name, col_def in new_columns.items():
        if col_name not in existing_cols:
            logger.info("迁移: %s 添加列 %s", table_name, col_name)
            await conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"))


async def _backfill_relation_entity_ids(conn) -> None:
    """为已有的 knowledge_base_relations 回填实体 ID。"""
    existing_cols = await _get_existing_columns(conn, "knowledge_base_relations")
    if "source_entity_id" not in existing_cols:
        return

    # 回填 NULL 实体 ID
    await conn.execute(
        text(
            "UPDATE knowledge_base_relations SET "
            "source_entity_id = (SELECT id FROM knowledge_base_entities "
            "WHERE name = from_entity AND kb_id = knowledge_base_relations.kb_id LIMIT 1), "
            "target_entity_id = (SELECT id FROM knowledge_base_entities "
            "WHERE name = to_entity AND kb_id = knowledge_base_relations.kb_id LIMIT 1) "
            "WHERE source_entity_id IS NULL OR target_entity_id IS NULL"
        )
    )


async def _backfill_agent_file_scope(conn) -> None:
    """为 agent_files 表回填 scope 字段：USER.md/MEMORY.md → user，其它 → agent。

    新增列时默认值是 'agent'，所以 WHERE 子句不能用 IS NULL——必须无条件更新，
    否则 USER.md/MEMORY.md 会停留在 'agent' 默认值上。
    """
    existing_cols = await _get_existing_columns(conn, "agent_files")
    if "scope" not in existing_cols:
        return
    await conn.execute(text(
        "UPDATE agent_files SET scope = CASE "
        "WHEN filename IN ('USER.md', 'MEMORY.md') THEN 'user' "
        "ELSE 'agent' END"
    ))


async def _fix_stuck_kb_status(conn) -> None:
    """修复卡在 'indexing' 状态的知识库——同步文档计数和状态。"""
    # 将 chunks / entities / relations 计数从实际文档数据同步到 KB 级别
    await conn.execute(text(
        "UPDATE knowledge_bases SET "
        "chunks_count = (SELECT COALESCE(SUM(chunks_count), 0) FROM knowledge_base_documents "
        "WHERE kb_id = knowledge_bases.id AND status = 'indexed'), "
        "entities_count = (SELECT COUNT(*) FROM knowledge_base_entities "
        "WHERE kb_id = knowledge_bases.id), "
        "relations_count = (SELECT COUNT(*) FROM knowledge_base_relations "
        "WHERE kb_id = knowledge_bases.id)"
    ))
    # 将没有活跃索引文档的 KB 状态设为 ready
    await conn.execute(text(
        "UPDATE knowledge_bases SET status = 'ready' "
        "WHERE status = 'indexing' "
        "AND id NOT IN ("
        "SELECT DISTINCT kb_id FROM knowledge_base_documents "
        "WHERE status NOT IN ('indexed', 'failed')"
        ")"
    ))
    logger.info("已修复卡住的 KB 状态和计数")


async def init_db():
    from db.base import Base
    from db.models.cron_job import CronJob  # noqa: F401  ensure table is registered

    # 断言 async_engine 不为 None，类型检查器会据此收窄类型
    assert async_engine is not None, "数据库引擎没有被初始化"

    logger.info("初始化数据库...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 运行时迁移——为已有表添加缺失列（无 Alembic 场景）
    async with async_engine.begin() as conn:
        await _migrate_table_columns(
            conn,
            "knowledge_base_documents",
            {
                "config": "JSON",
            },
        )
        await _migrate_table_columns(
            conn,
            "knowledge_base_relations",
            {
                "source_entity_id": "VARCHAR(36)",
                "target_entity_id": "VARCHAR(36)",
            },
        )
        await _migrate_table_columns(
            conn,
            "knowledge_base_entities",
            {
                "source_text": "VARCHAR(1024)",
                "char_start": "INTEGER",
                "char_end": "INTEGER",
            },
        )
        await _migrate_table_columns(
            conn,
            "agent_files",
            {
                "scope": "VARCHAR(16) DEFAULT 'agent' NOT NULL",
                # PostgreSQL 要求 BOOLEAN 列默认值用 FALSE，SQLite 用 0
                "read_only": (
                    "BOOLEAN DEFAULT FALSE NOT NULL"
                    if settings.DATABASE_BACKEND == "postgres"
                    else "BOOLEAN DEFAULT 0 NOT NULL"
                ),
                "org_id": "VARCHAR(64)",
            },
        )
        await _backfill_relation_entity_ids(conn)
        await _fix_stuck_kb_status(conn)
        await _backfill_agent_file_scope(conn)

    logger.info("数据库表已创建")

