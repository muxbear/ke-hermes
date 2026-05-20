import aiosqlite
from deepagents import create_deep_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.config import settings
from agent.models.llm import llm
from agent.tools.internet_search import internet_search

_graph = None


def get_graph():
    """Return the initialized graph. Must be called after init_graph()."""
    if _graph is None:
        raise RuntimeError("Graph not initialized. Call init_graph() first.")
    return _graph


async def init_graph():
    """Initialize the checkpointer and graph (called once at app startup)."""
    global _graph
    conn = aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
    checkpointer = AsyncSqliteSaver(conn)
    _graph = create_deep_agent(
        model=llm,
        tools=[internet_search],
        checkpointer=checkpointer,
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
    )


__all__ = ["get_graph", "init_graph"]
