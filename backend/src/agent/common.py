"""Agent 共享工具——消除 main_agent 与 subagents_operate 之间的代码重复。

所有关键导入使用懒加载以避免循环导入（agent ↔ api ↔ core ↔ db 之间的复杂依赖）。
"""

from ast import Raise
import logging

from agent import tools as agent_tools

logger = logging.getLogger(__name__)


def get_tool_registry() -> dict[str, object]:
    """构建工具名称字符串到可调用工具函数的映射。"""
    registry: dict[str, object] = {}
    for name in agent_tools.__all__:
        tool = getattr(agent_tools, name, None)
        if callable(tool):
            registry[name] = tool
    return registry


async def resolve_model(
    provider_id: str | None,
    model_id: str | None,
    *,
    fallback_to_settings: bool = False,
):
    """根据 provider_id 和 model_id 解析 LLM 实例。

    解析失败时抛出异常。

    Args:
        provider_id: 提供商 ID。
        model_id: 模型 ID。
        fallback_to_settings: 若提供商 api_key 为空，是否回退到 settings 中的默认 key。
    """
    # 懒加载以避免循环导入
    from langchain_openai import ChatOpenAI
    from pydantic import SecretStr
    from sqlalchemy import select

    from agent.config import settings
    from agent.models.llm import llm as default_llm
    from core.security import decrypt_api_key
    from db.engine import async_session
    from db.models.ai_model import AIModel
    from db.models.provider import Provider

    if not provider_id or not model_id:
        logger.warning(f"未配置提供商或模型，使用默认 LLM {default_llm}")
        return default_llm

    async with async_session() as session:
        try:
            provider = (
                await session.execute(
                    select(Provider).where(Provider.id == provider_id)
                )
            ).scalar_one_or_none()

            if provider is None:
                raise RuntimeError(f"提供商 {provider_id} 未找到，使用默认 LLM")

            decrypted_key = decrypt_api_key(provider.api_key)
            if not decrypted_key:
                raise RuntimeError(f"模型提供商 {provider} 未配置 api_key ")
            else:
                api_key = decrypted_key

            model = (
                await session.execute(
                    select(AIModel).where(
                        AIModel.id == model_id, AIModel.provider_id == provider_id
                    )
                )
            ).scalar_one_or_none()

            if model is None:
                raise RuntimeError(f"模型提供商 {provider_id} 未配置模型 {provider_id}")

            return ChatOpenAI(
                model=model.name,
                api_key=SecretStr(api_key),
                base_url=provider.api_base,
            )
        except Exception:
            logger.exception("解析模型失败，使用默认 LLM")
            raise
