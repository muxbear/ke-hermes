from deepagents import create_deep_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

import aiosqlite

from agent.context.context import Context
from agent.config import settings
from agent.models.llm import llm
from agent.subagents import research_subagent

from deepagents.backends import FilesystemBackend

_graph = None
_checkpointer_pool = None

WORKSPACE = settings.WORKSPACE

def get_graph():
    """Return the initialized graph. Must be called after init_graph()."""
    if _graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() first.")
    return _graph

async def init_graph():
    """Initialize the checkpointer and graph (called once at app startup)."""
    global _graph, _checkpointer_pool
    
    backend = settings.CHECKPOINT_BACKEND

    if backend == "sqlite":
        conn = await aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
        checkpointer = AsyncSqliteSaver(conn)
    elif backend == "postgres":
        _checkpointer_pool = AsyncConnectionPool(
            conninfo=settings.CHECKPOINT_DB_URL,
            open=False,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        )
        await _checkpointer_pool.open()
        checkpointer = AsyncPostgresSaver(_checkpointer_pool)
        await checkpointer.setup()
    else:
        raise ValueError(
              f"Unknown CHECKPOINT_BACKEND: '{backend}'. Expected 'sqlite' or 'postgres'."
        )

    subagents = [research_subagent]

    _graph = create_deep_agent(
        name="main-agent",
        model=llm,
        context_schema=Context,
        checkpointer=checkpointer,
        backend=FilesystemBackend(root_dir=WORKSPACE, virtual_mode=True),
        subagents=subagents,
        # skills=["/skills/"],
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求委派对应的子智能体进行处理。",
    )

async def shutdown_graph():
    global _checkpointer_pool
    if _checkpointer_pool is not None:
        await _checkpointer_pool.close()
        _checkpointer_pool = None

__all__ = ["get_graph", "init_graph", "shutdown_graph"]
