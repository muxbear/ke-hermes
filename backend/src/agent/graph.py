import logging

from datetime import timedelta

from agent.sandbox.opensandbox_backend import OpenSandBoxBackend
from agent.sandbox.opensandbox_operate import create_sandboxsync
from agent.subagents.subagents_operate import create_subagents
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import aiosqlite

from langchain.agents.middleware import Runtime

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore

from agent.context.context import Context
from agent.config import settings
from agent.models.llm import llm

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StoreBackend

import os

logger = logging.getLogger(__name__)

_graph = None
_conn_pool = None
_checkpointer = None
_store = None

WORKSPACE = settings.WORKSPACE
MEMORIES = os.path.join(WORKSPACE, "memories")

def get_graph():
    """Return the initialized graph. Must be called after init_graph()."""
    if _graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() first.")
    return _graph

def get_checkpointer():
    if _checkpointer is None:
        raise RuntimeError("Checkpointer not initialized. Call init_graph() first.")
    return _checkpointer

async def init_graph():
    """Initialize the checkpointer and graph (called once at app startup)."""
    global _graph, _conn_pool, _checkpointer, _store
    
    backend = settings.CHECKPOINT_BACKEND

    if backend == "sqlite":
        conn = await aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
        _checkpointer = AsyncSqliteSaver(conn)
        _store = InMemoryStore()
    elif backend == "postgres":
        _conn_pool = AsyncConnectionPool(
            conninfo=settings.CHECKPOINT_DB_URL,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        )
        await _conn_pool.open()

        _checkpointer = AsyncPostgresSaver(_conn_pool)
        await _checkpointer.setup()

        _store = AsyncPostgresStore(_conn_pool)
        await _store.setup() # 会自动创建 store 表和 store_migrations 表
    else:
        raise ValueError(
              f"Unknown CHECKPOINT_BACKEND: '{backend}'. Expected 'sqlite' or 'postgres'."
        )

    # 创建子代理
    subagents = await create_subagents()
    logger.info(f"从配置中加载到 {len(subagents)} 个子智能体。")
    
    # 创建沙盒
    sandbox = create_sandboxsync()
    # 创建沙盒后端
    sandbox_backend = OpenSandBoxBackend(sandbox=sandbox)

    _graph = create_deep_agent(
        name="main-agent",
        model=llm,
        checkpointer=_checkpointer,
        store=_store,
        context_schema=Context,
        memory=["/memories/AGENT.md"],
        skills=["/skills/"],
        backend=CompositeBackend(
            default=sandbox_backend,
            routes={
                "/memories/": StoreBackend(
                    namespace=lambda ctx: (
                        ctx.runtime.context.user_id,
                    ),
                ),
            }
        ),
        subagents=subagents,
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求委派对应的子智能体进行处理。",
    )

async def shutdown_graph():
    global _conn_pool
    if _conn_pool is not None:
        await _conn_pool.close()
        _conn_pool = None

__all__ = ["get_graph", "get_checkpointer", "init_graph", "shutdown_graph"]
