import aiosqlite
from deepagents import create_deep_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from agent.config import settings
from agent.models.llm import llm
from agent.tools.internet_search import internet_search

from deepagents.backends import FilesystemBackend

import os

_graph = None
_checkpointer_pool = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
PROJECT_ROOT = os.path.join(PROJECT_ROOT, "workspace")
print(f'工作路径 = {PROJECT_ROOT}')

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

    _graph = create_deep_agent(
        model=llm,
        tools=[internet_search],
        checkpointer=checkpointer,
        backend=FilesystemBackend(root_dir=PROJECT_ROOT, virtual_mode=True),
        # skills=["/skills/"],
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
    )

async def shutdown_graph():
    global _checkpointer_pool
    if _checkpointer_pool is not None:
        await _checkpointer_pool.close()
        _checkpointer_pool = None

__all__ = ["get_graph", "init_graph", "shutdown_graph"]
