import logging

from sqlalchemy import select

from agent import tools as agent_tools

logger = logging.getLogger(__name__)


def _get_tool_registry() -> dict[str, object]:
    """构建工具名称字符串到可调用工具函数的映射。"""
    registry: dict[str, object] = {}
    for name in agent_tools.__all__:
        tool = getattr(agent_tools, name, None)
        if callable(tool):
            registry[name] = tool
    return registry


async def _resolve_model(provider_id: str | None, model_id: str | None):
    """从数据库中解析子智能体的模型配置，失败时回退到默认的 DeepSeek 模型。"""
    from langchain_openai import ChatOpenAI

    from agent.models import llm as default_llm
    from db.engine import async_session
    from db.models.ai_model import AIModel
    from db.models.provider import Provider

    if not provider_id or not model_id:
        return default_llm

    async with async_session() as session:
        try:
            provider = (
                await session.execute(
                    select(Provider).where(Provider.id == provider_id)
                )
            ).scalar_one_or_none()

            if provider is None:
                logger.warning("提供商 '%s' 未找到，使用默认 LLM", provider_id)
                return default_llm

            from core.security import decrypt_api_key

            decrypted_key = decrypt_api_key(provider.api_key)
            if not decrypted_key:
                logger.warning(
                    "提供商 '%s' 没有 api_key，使用默认 LLM", provider_id,
                )
                return default_llm

            model = (
                await session.execute(
                    select(AIModel).where(
                        AIModel.id == model_id, AIModel.provider_id == provider_id
                    )
                )
            ).scalar_one_or_none()

            if model is None:
                logger.warning(
                    "模型 '%s' 在提供商 '%s' 未找到，使用默认 LLM",
                    model_id, provider_id,
                )
                return default_llm

            from pydantic import SecretStr

            return ChatOpenAI(
                model=model.name,
                api_key=SecretStr(decrypted_key),
                base_url=provider.api_base,
            )
        except Exception:
            logger.exception("解析模型失败，使用默认 LLM")
            return default_llm


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
            "model": await _resolve_model(info.provider_id, info.model_id),
            "system_prompt": system_prompt,
            "skills": [f"/skills/{info.id}/"],
        })

    logger.info("从数据库加载了 %d 个子智能体", len(subagents))
    return subagents
