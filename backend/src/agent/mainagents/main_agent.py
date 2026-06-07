"""主智能体工厂 — 根据数据库配置创建主智能体。"""

import logging

from sqlalchemy import select

from agent.config import settings
from agent.context.context import Context
from agent.models.llm import llm as default_llm
from agent.sandbox.opensandbox_backend import OpenSandBoxBackend
from agent.sandbox.opensandbox_operate import create_sandboxsync
from agent.subagents.subagents_operate import create_subagents
from agent import tools as agent_tools
from api.agents.service import list_agents
from db.engine import async_session
from db.models.ai_model import AIModel
from db.models.provider import Provider
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StoreBackend
from langchain_openai import ChatOpenAI

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
    """根据 provider_id 和 model_id 解析 LLM 实例。

    解析失败时回退到 settings 中配置的默认 DeepSeek LLM。
    """
    if not provider_id or not model_id:
        logger.info("未配置提供商/模型，使用默认 LLM")
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

            model = (
                await session.execute(
                    select(AIModel).where(
                        AIModel.id == model_id, AIModel.provider_id == provider_id
                    )
                )
            ).scalar_one_or_none()

            if model is None:
                logger.warning(
                    "模型 '%s' 在提供商 '%s' 中未找到，使用默认 LLM",
                    model_id,
                    provider_id,
                )
                return default_llm

            return ChatOpenAI(
                model=model.name,
                api_key=provider.api_key or settings.DEEPSEEK_API_KEY,
                base_url=provider.api_base,
            )
        except Exception:
            logger.exception("解析模型失败，使用默认 LLM")
            return default_llm


async def create_main_agent(checkpointer=None, store=None):
    """从数据库配置创建主智能体。

    从 agents 表中查询活跃的主智能体（type == 'main'），解析其模型、工具、
    system_prompt、子智能体等配置，然后通过 create_deep_agent() 组装出完整的
    主智能体。

    Args:
        checkpointer: LangGraph 检查点实例（AsyncSqliteSaver 或 AsyncPostgresSaver），生产环境必须传入。
        store: LangGraph 存储实例（InMemoryStore 或 AsyncPostgresStore），生产环境必须传入。

    Returns:
        配置完成的 deep agent 实例。

    Raises:
        RuntimeError: 数据库中不存在活跃的主智能体时抛出。
    """
    # 1. 从数据库查询主智能体
    async with async_session() as session:
        try:
            result = await list_agents(session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    main_agents = [
        a for a in result.agents if a.type == "main" and a.status == "active"
    ]
    if not main_agents:
        raise RuntimeError("数据库中不存在活跃的主智能体")

    agent_info = main_agents[0]
    logger.info(
        "正在创建主智能体 '%s'（id=%s, 工具=%d, 提示词=%d, 文件=%d）",
        agent_info.name,
        agent_info.id,
        len(agent_info.tools),
        len(agent_info.prompts),
        len(agent_info.files),
    )

    # 2. 解析 LLM 模型
    model = await _resolve_model(agent_info.provider_id, agent_info.model_id)

    # 3. 将工具名称字符串解析为可调用函数
    tool_registry = _get_tool_registry()
    tools = []
    for name in agent_info.tools:
        fn = tool_registry.get(name)
        if fn is not None:
            tools.append(fn)
        else:
            logger.warning("工具 '%s' 在注册表中未找到，已跳过", name)

    # 4. 根据智能体提示词构建 system_prompt
    if agent_info.prompts:
        system_prompt = "\n\n".join(agent_info.prompts)
    else:
        system_prompt = (
            "你是 ke-hermes 通用智能体，请根据用户的需求委派对应的子智能体进行处理。"
        )

    # 5. 从数据库加载子智能体
    subagents = await create_subagents()
    logger.info("已加载 %d 个子智能体", len(subagents))

    # 6. 创建沙箱后端
    sandbox = create_sandboxsync()
    sandbox_backend = OpenSandBoxBackend(sandbox=sandbox)
    backend = CompositeBackend(
        default=sandbox_backend,
        routes={
            # "/skills/": FilesystemBackend(root_dir=settings.SKILLS_ROOT),
            "/memories/": StoreBackend(
                namespace=lambda ctx: (ctx.runtime.context.user_id,),
            ),
        },
    )

    # 7. 根据智能体文件名称构建记忆路径
    if agent_info.files:
        memory = [f"/memories/{f}" for f in agent_info.files]
    else:
        memory = ["/memories/AGENT.md"]

    # 8. 创建 deep agent
    agent = create_deep_agent(
        name=agent_info.name,
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        store=store,
        context_schema=Context,
        # skills=["/skills/"],
        memory=memory,
        backend=backend,
        subagents=subagents,
        system_prompt=system_prompt,
    )

    logger.info("主智能体 '%s' 创建成功", agent_info.name)
    return agent
