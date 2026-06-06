import logging

from agent import tools as agent_tools

logger = logging.getLogger(__name__)


def _get_tool_registry() -> dict[str, object]:
    """Build a mapping from tool name strings to callable tool functions."""
    registry: dict[str, object] = {}
    for name in agent_tools.__all__:
        tool = getattr(agent_tools, name, None)
        if callable(tool):
            registry[name] = tool
    return registry


def _resolve_model() -> object:
    """Resolve default model for sub-agents."""
    from agent.models import qwen_llm

    return qwen_llm


async def create_subagents() -> list[dict]:
    """从数据库表读取子智能体的配置组织成 subagents 字典数组.

    例如：
    [
        {
            "name": "research-agent",
            "description": "使用网络搜索进行深入研究并综合分析结果",
            "tools": [internet_search],
            "skills": '/skills/',
            "model": qwen_llm,
            "system_prompt": ''
        }
    ]
    """
    # Lazy imports to avoid circular dependencies at module level
    from api.agents.service import list_agents  # noqa: PLC0415
    from db.engine import async_session  # noqa: PLC0415

    tool_registry = _get_tool_registry()

    async with async_session() as session:
        try:
            result = await list_agents(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    sub_agent_infos = [
        a for a in result.agents
        if a.type == "sub" and a.status == "active"
    ]

    if not sub_agent_infos:
        logger.info("No active sub-agents found in database")
        return []

    subagents: list[dict] = []
    for info in sub_agent_infos:
        tools = []
        for name in info.tools:
            fn = tool_registry.get(name)
            if fn is not None:
                tools.append(fn)
            else:
                logger.warning("Tool '%s' not found in registry, skipping", name)

        system_prompt = "\n\n".join(info.prompts) if info.prompts else ""

        subagents.append({
            "name": info.name,
            "description": info.description or "",
            "tools": tools,
            "model": _resolve_model(),
            "system_prompt": system_prompt,
        })

    logger.info("Loaded %d sub-agent(s) from database", len(subagents))
    return subagents
