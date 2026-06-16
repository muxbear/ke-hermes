import logging

from sqlalchemy import select

from agent.common import get_tool_registry, resolve_model

logger = logging.getLogger(__name__)


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
    # 懒加载导入，避免模块级别的循环依赖
    from api.agents.service import list_agents  # noqa: PLC0415
    from db.engine import async_session  # noqa: PLC0415

    tool_registry = get_tool_registry()

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
        logger.info("数据库中未找到活跃的子智能体")
        return []

    subagents: list[dict] = []
    for info in sub_agent_infos:
        tools = []
        for name in info.tools:
            fn = tool_registry.get(name)
            if fn is not None:
                tools.append(fn)
            else:
                logger.warning("工具 '%s' 在注册表中未找到，跳过", name)

        system_prompt = info.system_prompt or ""

        subagents.append({
            "name": info.name,
            "description": info.description or "",
            "tools": tools,
            "model": await resolve_model(info.provider_id, info.model_id),
            "system_prompt": system_prompt,
            "skills": [f"/skills/{info.id}/"],
        })

    logger.info("从数据库加载了 %d 个子智能体", len(subagents))
    return subagents
