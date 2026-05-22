import aiosqlite
from deepagents import create_deep_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agent.config import settings
from agent.models.llm import llm
from agent.tools.internet_search import internet_search

from deepagents.backends import FilesystemBackend, LocalShellBackend

import os

_graph = None

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


python_paths = [
    r"D:\opt\Python\Python311",
    r"D:\opt\Python\Python311\Scripts"
]
system_path = os.environ.get("PATH", "")
# 用分号分隔
env_path = ";".join(python_paths) + ";" + system_path if system_path else ";".join(python_paths)

async def init_graph():
    """Initialize the checkpointer and graph (called once at app startup)."""
    global _graph
    conn = aiosqlite.connect(settings.CHECKPOINT_DB_PATH)
    checkpointer = AsyncSqliteSaver(conn)
    _graph = create_deep_agent(
        model=llm,
        tools=[internet_search],
        checkpointer=checkpointer,
        # backend=FilesystemBackend(root_dir=PROJECT_ROOT, virtual_mode=True),
        backend=LocalShellBackend(root_dir=PROJECT_ROOT, env={"PATH": env_path}),
        skills=["/skills/"],
        system_prompt="你是 ke-hermes 通用智能体，请根据用户的需求提供准确、有用的回答。",
    )


__all__ = ["get_graph", "init_graph"]
