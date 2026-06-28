import logging
from typing import Any

from agent.mainagents import create_main_agent
from agent.sandbox.sandbox_manager import SandboxManager
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

import aiosqlite

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore

from agent.config import settings

logger = logging.getLogger(__name__)

_graph = None
_conn_pool: AsyncConnectionPool[AsyncConnection[DictRow]] | None = None
_checkpointer = None
_store = None
_sandbox_manager = None


def get_graph():
    """返回已初始化的图。必须在 init_graph() 之后调用。"""
    if _graph is None:
        raise RuntimeError("图未初始化，请先调用 init_graph()。")
    return _graph


def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("检查点未初始化，请先调用 init_graph()。")
    return _checkpointer


def get_store() -> Any:
    """返回已初始化的 LangGraph Store。必须在 init_graph() 之后调用。"""
    if _store is None:
        raise RuntimeError("Store 未初始化，请先调用 init_graph()。")
    return _store


async def init_graph():
    """初始化检查点和图（在应用启动时调用一次）。"""
    global _graph, _conn_pool, _checkpointer, _store, _sandbox_manager

    checkpoint_backend = settings.CHECKPOINT_BACKEND

    if checkpoint_backend == "sqlite":
        conn = await aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
        _checkpointer = AsyncSqliteSaver(conn)
        _store = InMemoryStore()
    elif checkpoint_backend == "postgres":
        _conn_pool = AsyncConnectionPool(
            conninfo=settings.CHECKPOINT_DB_URL,
            open=False,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
        )
        await _conn_pool.open()

        _checkpointer = AsyncPostgresSaver(_conn_pool)
        await _checkpointer.setup()

        _store = AsyncPostgresStore(_conn_pool)
        await _store.setup()  # 会自动创建 store 表和 store_migrations 表
    else:
        raise ValueError(
            f"未知的 CHECKPOINT_BACKEND: '{checkpoint_backend}'，期望 'sqlite' 或 'postgres'。"
        )

    _sandbox_manager = SandboxManager(
        extra_domains=settings.sandbox_allowed_domains_list,
    )
    _sandbox_manager.start_cleanup()

    # 创建主智能体
    _graph = await create_main_agent(
        checkpointer=_checkpointer,
        store=_store,
        sandbox_manager=_sandbox_manager,
    )


async def shutdown_graph():
    global _conn_pool, _sandbox_manager
    if _sandbox_manager is not None:
        _sandbox_manager.shutdown()
        _sandbox_manager = None
    if _conn_pool is not None:
        await _conn_pool.close()
        _conn_pool = None


__all__ = ["get_graph", "get_checkpointer", "get_store", "init_graph", "shutdown_graph"]
