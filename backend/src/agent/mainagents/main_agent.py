"""主智能体工厂 — 使用建造者模式根据数据库配置创建主智能体。"""

import logging

from agent.common import get_tool_registry, resolve_model  # noqa: F401  re-export for callers

logger = logging.getLogger(__name__)


async def create_main_agent(checkpointer=None, store=None, sandbox_manager=None):
    """从数据库配置创建主智能体——内部委托给 AgentBuilder。

    保持与旧版本的签名兼容，内部使用建造者模式逐步构建。

    Args:
        checkpointer: LangGraph 检查点实例。
        store: LangGraph 存储实例。
        sandbox_manager: 可选 SandboxManager 实例。

    Returns:
        配置完成的 deep agent 实例。
    """
    from agent.builders.agent_builder import AgentBuilder
    from db.engine import async_session

    async with async_session() as session:
        builder = AgentBuilder()
        await builder.with_agent_from_db(session)

    await builder.with_model()
    await builder.with_tools()
    builder.with_system_prompt()
    await builder.with_subagents()
    builder.with_sandbox(sandbox_manager=sandbox_manager)
    builder.with_backend()
    builder.with_memory()
    builder.with_middleware()
    return builder.build(checkpointer=checkpointer, store=store)
