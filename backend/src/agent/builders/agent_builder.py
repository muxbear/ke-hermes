"""Agent 建造者模式 — 将单块 create_main_agent() 分解为可组合的构建步骤。

使用方式:
    agent = await (
        AgentBuilder()
        .with_agent_from_db()
        .with_model()
        .with_tools()
        .with_system_prompt()
        .with_subagents()
        .with_sandbox()
        .with_backend()
        .with_memory()
        .with_middleware()
        .build(checkpointer, store)
    )
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StoreBackend
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.common import get_tool_registry, resolve_model
from agent.config import settings
from agent.context.context import Context
from agent.memory.scopes import (
    DEFAULT_ORG_ID,
    MemoryScope,
    build_memory_path,
    infer_scope,
)
from agent.middleware.skill_sandbox_sync import SkillSandboxSyncMiddleware
from agent.middleware.template_copy import TemplateCopyMiddleware
from agent.sandbox.sandbox_manager import SandboxManager
from agent.sandbox.user_aware_sandbox_backend import UserAwareSandboxBackend
from agent.subagents.subagents_operate import create_subagents
from db.models.agent_file import AgentFile

logger = logging.getLogger(__name__)


class AgentBuilder:
    """分步构建 Deep Agent 的建造者。

    将原来 118 行的 create_main_agent() 分解为独立的、可测试的构建步骤。
    每个 with_* 方法返回 self 以支持链式调用。
    """

    def __init__(self) -> None:
        self._agent_id: str = ""
        self._agent_info: Any = None
        self._model: Any = None
        self._tools: list = []
        self._system_prompt: str = ""
        self._subagents: list[dict] = []
        self._backend: Any = None
        self._sandbox_manager: SandboxManager | None = None
        self._sandbox_backend: Any = None
        self._memory: list[str] = []
        self._middleware: list = []
        self._skills_root: str = ""

    async def with_agent_from_db(self, db: AsyncSession) -> "AgentBuilder":
        """从数据库查询活跃的主智能体配置。"""
        from api.agents.service import list_agents as list_agents_svc

        try:
            result = await list_agents_svc(db)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        main_agents = [
            a for a in result.agents if a.type == "main" and a.status == "active"
        ]
        if not main_agents:
            raise RuntimeError("数据库中不存在活跃的主智能体")

        self._agent_info = main_agents[0]
        self._agent_id = self._agent_info.id
        logger.info(
            "正在创建主智能体 '%s'（id=%s, 工具=%d, 文件=%d）",
            self._agent_info.name,
            self._agent_info.id,
            len(self._agent_info.tools),
            len(self._agent_info.files),
        )
        return self

    async def with_model(self) -> "AgentBuilder":
        """通过共享的 resolve_model 解析 LLM 实例。"""
        if self._agent_info is None:
            raise RuntimeError("必须先调用 with_agent_from_db()")

        self._model = await resolve_model(
            self._agent_info.provider_id,
            self._agent_info.model_id,
            fallback_to_settings=True,
        )
        return self

    async def with_tools(self) -> "AgentBuilder":
        """将工具名称解析为可调用函数。"""
        if self._agent_info is None:
            raise RuntimeError("必须先调用 with_agent_from_db()")

        tool_registry = get_tool_registry()
        for name in self._agent_info.tools:
            fn = tool_registry.get(name)
            if fn is not None:
                self._tools.append(fn)
            else:
                logger.warning("工具 '%s' 在注册表中未找到，已跳过", name)
        return self

    def with_system_prompt(self, default: str | None = None) -> "AgentBuilder":
        """设置系统提示词。"""
        if self._agent_info is None:
            raise RuntimeError("必须先调用 with_agent_from_db()")
        self._system_prompt = self._agent_info.system_prompt
        return self

    async def with_subagents(self) -> "AgentBuilder":
        """从数据库加载子智能体。"""
        self._subagents = await create_subagents()
        return self

    def with_sandbox(
        self,
        sandbox_manager: SandboxManager | None = None,
    ) -> "AgentBuilder":
        """创建沙箱后端（每个用户独立沙箱，带 TTL 管理）。

        Args:
            sandbox_manager: 可选外部 SandboxManager。传入时由调用方管理生命周期。
        """
        self._skills_root = os.path.join(settings.WORKSPACE, "skills")

        if sandbox_manager is not None:
            self._sandbox_manager = sandbox_manager
        else:
            self._sandbox_manager = SandboxManager(
                extra_domains=settings.sandbox_allowed_domains_list,
            )
            self._sandbox_manager.start_cleanup()

        self._sandbox_backend = UserAwareSandboxBackend(
            sandbox_manager=self._sandbox_manager
        )
        return self

    def with_backend(self) -> "AgentBuilder":
        """构建组合后端（sandbox + 四作用域 StoreBackend + /skills/ FilesystemBackend）。

        所有记忆作用域统一在 /memories/ 下，namespace 使用构建时确定的 agent_id：
        - /memories/agent/    → namespace=(agent_id,)                   全用户共享
        - /memories/user/     → namespace=(agent_id, user_id)           按用户隔离
        - /memories/mixture/  → namespace=(agent_id, user_id, "mixture") 自定义文件
        - /memories/policies/ → namespace=(org_id,)                     组织级只读
        - /skills/            → FilesystemBackend
        """
        if self._sandbox_backend is None:
            raise RuntimeError("必须先调用 with_sandbox()")

        agent_id = self._agent_id

        self._backend = CompositeBackend(
            default=self._sandbox_backend,
            routes={
                "/memories/agent/": StoreBackend(
                    namespace=lambda rt: (agent_id,),
                ),
                "/memories/user/": StoreBackend(
                    namespace=lambda rt: (
                        agent_id,
                        cast(Any, rt).runtime.context.user_id,
                    ),
                ),
                "/memories/mixture/": StoreBackend(
                    namespace=lambda rt: (
                        agent_id,
                        cast(Any, rt).runtime.context.user_id,
                        "mixture",
                    ),
                ),
                "/memories/policies/": StoreBackend(
                    namespace=lambda rt: (
                        getattr(
                            cast(Any, rt).runtime.context, "org_id", ""
                        ) or DEFAULT_ORG_ID,
                    ),
                ),
                "/skills/": FilesystemBackend(
                    root_dir=self._skills_root, virtual_mode=True
                ),
            },
        )
        return self

    async def with_memory(self, db: AsyncSession) -> "AgentBuilder":
        """根据智能体文件作用域构建记忆路径列表。

        从 AgentFile 表读取每个文件的 scope，按 scope 拼接对应前缀路径。
        若文件无 scope 记录（旧数据），按文件名推断并回填。
        """
        if self._agent_info is None:
            raise RuntimeError("必须先调用 with_agent_from_db()")

        files = (
            self._agent_info.files
            if isinstance(self._agent_info.files, list)
            else []
        )

        if not files:
            self._memory = [build_memory_path(MemoryScope.AGENT, "AGENTS.md")]
            return self

        # 查询每个文件的 scope
        stmt = select(AgentFile).where(
            AgentFile.agent_id == self._agent_id,
            AgentFile.filename.in_(files),
        )
        rows = (await db.execute(stmt)).scalars().all()
        scope_by_filename: dict[str, MemoryScope] = {}
        for row in rows:
            try:
                scope_by_filename[row.filename] = (
                    MemoryScope(row.scope) if row.scope else infer_scope(row.filename)
                )
            except ValueError:
                scope_by_filename[row.filename] = infer_scope(row.filename)

        self._memory = [
            build_memory_path(
                scope_by_filename.get(f, infer_scope(f)),
                f,
            )
            for f in files
        ]
        return self

    def with_middleware(self) -> "AgentBuilder":
        """创建中间件链（模板复制 → 技能沙盒同步）。"""
        if self._sandbox_manager is None:
            raise RuntimeError("必须先调用 with_sandbox()")
        self._middleware = []

        # 模板复制中间件：首次对话时将 USER/MIXTURE 模板复制到用户命名空间
        template_paths = [
            p
            for p in self._memory
            if p.startswith("/memories/user/")
            or p.startswith("/memories/mixture/")
        ]
        if template_paths:
            self._middleware.append(
                TemplateCopyMiddleware(
                    agent_id=self._agent_id,
                    template_paths=template_paths,
                )
            )

        self._middleware.append(
            SkillSandboxSyncMiddleware(
                sandbox_manager=self._sandbox_manager,
                skills_root=self._skills_root,
                agent_id=self._agent_id,
            )
        )
        return self

    def build(self, checkpointer=None, store=None):
        """组装最终步骤，创建并返回 deep agent 实例。

        Args:
            checkpointer: LangGraph 检查点实例。
            store: LangGraph 存储实例。
        """
        if self._agent_info is None:
            raise RuntimeError("必须先调用 with_agent_from_db()")

        agent = create_deep_agent(
            name=self._agent_info.name,
            model=self._model,
            tools=self._tools,
            checkpointer=checkpointer,
            store=store,
            context_schema=Context,
            skills=[f"/skills/{self._agent_id}/"],
            memory=self._memory,
            backend=self._backend,
            subagents=cast(Any, self._subagents),
            system_prompt=self._system_prompt,
            middleware=self._middleware,  # type: ignore[list-item]
        )

        logger.info(f"主智能体 {self._agent_info.name} 创建成功")
        return agent
