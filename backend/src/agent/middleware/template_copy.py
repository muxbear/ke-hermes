"""模板拷贝中间件 — 首次对话时将 USER/MIXTURE 模板复制到用户命名空间。

管理员在 DB 中配置的 USER/MIXTURE 作用域文件作为模板存储在
``(agent_id, "__template__")`` 命名空间，运行时 Agent 从
``(agent_id, user_id)`` 读取。本中间件在用户首次对话时自动将模板复制到
用户命名空间，实现「模板→用户实例」的语义。
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Annotated, Any, NotRequired

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    PrivateStateAttr,
)

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
    from langgraph.runtime import Runtime

from agent.memory.scopes import TEMPLATE_USER_ID

logger = logging.getLogger(__name__)


class TemplateCopyState(AgentState):
    """模板拷贝中间件状态 — 记录当前会话是否已完成模板复制。"""

    _templates_copied: NotRequired[Annotated[bool, PrivateStateAttr]]


class TemplateCopyMiddleware(AgentMiddleware[TemplateCopyState, Any, Any]):
    """首次对话时将 USER/MIXTURE 模板文件复制到用户命名空间。

    在每个会话首次执行时检查用户命名空间是否已有对应文件；
    若不存在则从 ``__template__`` 命名空间复制。后续对话跳过。
    """

    state_schema = TemplateCopyState

    def __init__(self, *, agent_id: str, template_paths: list[str]) -> None:
        """初始化模板拷贝中间件。

        Args:
            agent_id: 智能体 ID。
            template_paths: USER/MIXTURE 作用域的虚拟路径列表，
                如 ``["/memories/user/preferences.md"]``。
        """
        self._agent_id = agent_id
        self._template_paths = template_paths

    async def abefore_agent(  # type: ignore[override]
        self,
        state: TemplateCopyState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> dict[str, bool] | None:
        """在智能体执行前复制模板文件到用户命名空间。"""
        if state.get("_templates_copied"):
            return None

        store = getattr(runtime, "store", None)
        if store is None:
            return {"_templates_copied": True}

        if runtime.context is None:
            return {"_templates_copied": True}

        user_id: str = runtime.context.user_id

        for path in self._template_paths:
            # Store key 为 "/filename"（CompositeBackend 剥离路由前缀后保留前导 /）
            store_key = f"/{path.rsplit('/', 1)[-1]}" if "/" in path else f"/{path}"
            template_ns: tuple[str, ...]
            user_ns: tuple[str, ...]

            if path.startswith("/memories/user/"):
                template_ns = (self._agent_id, TEMPLATE_USER_ID)
                user_ns = (self._agent_id, user_id)
            elif path.startswith("/memories/mixture/"):
                template_ns = (self._agent_id, TEMPLATE_USER_ID, "mixture")
                user_ns = (self._agent_id, user_id, "mixture")
            else:
                continue

            # 用户已有副本则跳过
            try:
                if await store.aget(user_ns, store_key) is not None:
                    continue
            except Exception:
                pass

            # 从模板命名空间复制
            try:
                template = await store.aget(template_ns, store_key)
            except Exception:
                logger.debug("模板 %s 不存在于命名空间 %s", store_key, template_ns)
                continue

            if template is None:
                continue

            try:
                await store.aput(user_ns, store_key, template.value)
                logger.info("已将模板 %s 复制到用户 %s 命名空间", store_key, user_id)
            except Exception:
                logger.exception("复制模板 %s 到用户 %s 失败", store_key, user_id)

        return {"_templates_copied": True}
