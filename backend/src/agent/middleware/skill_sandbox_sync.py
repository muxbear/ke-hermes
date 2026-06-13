"""技能沙盒同步中间件 — 在智能体执行前将技能文件上传到沙盒。"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING, Annotated, Any, NotRequired, cast

import yaml
from deepagents.backends.filesystem import FilesystemBackend
from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    PrivateStateAttr,
)
from opensandbox.adapters.egress_adapter import EgressAdapter
from opensandbox.constants import DEFAULT_EGRESS_PORT
from opensandbox.models import NetworkRule

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
    from langgraph.runtime import Runtime

from agent.sandbox.sandbox_manager import SandboxManager

logger = logging.getLogger(__name__)


class SkillSandboxSyncState(AgentState):
    """技能同步中间件状态 — 记录沙盒同步标记。"""

    _skills_synced: NotRequired[Annotated[str | None, PrivateStateAttr]]


class SkillSandboxSyncMiddleware(AgentMiddleware[SkillSandboxSyncState, Any, Any]):
    """在智能体执行前将技能文件同步到用户沙盒。

    使用沙盒 ID 作为同步标记，避免每次对话都重复上传。当沙盒因 TTL 过期
    被重建后，会自动检测新沙盒 ID 并重新同步。
    """

    state_schema = SkillSandboxSyncState

    def __init__(
        self,
        *,
        sandbox_manager: SandboxManager,
        skills_root: str,
        agent_id: str,
    ) -> None:
        """初始化技能同步中间件。

        Args:
            sandbox_manager: 沙盒管理器，用于获取用户沙盒后端。
            skills_root: 本地技能目录根路径，例如 ``{WORKSPACE}/skills``。
            agent_id: 当前智能体 ID，用于定位技能子目录。
        """
        self._sandbox_manager = sandbox_manager
        self._agent_id = agent_id
        self._local_fs: FilesystemBackend = FilesystemBackend(
            root_dir=skills_root, virtual_mode=True
        )

    async def abefore_agent(  # type: ignore[override]
        self,
        state: SkillSandboxSyncState,
        runtime: Runtime,
        config: RunnableConfig,
    ) -> dict[str, str] | None:
        """在智能体执行前同步技能文件到沙盒。

        检查当前沙盒 ID 是否与上次同步一致；不一致则遍历本地技能目录，
        将所有文件上传到沙盒。
        """
        if runtime.context is None:
            logger.warning("无法获取用户上下文，跳过技能同步")
            return None
        user_id: str = runtime.context.user_id
        backend = await asyncio.to_thread(
            self._sandbox_manager.get_or_create_backend, user_id
        )
        sandbox_id: str = backend.id

        # 已同步到当前沙盒则跳过
        if state.get("_skills_synced") == sandbox_id:
            return None

        # 收集本地技能目录下的所有文件
        files = await self._collect_skill_files(f"/{self._agent_id}/")
        if not files:
            logger.info("智能体 %s 无技能文件需要同步", self._agent_id)
            return {"_skills_synced": sandbox_id}

        # 转换为沙盒路径并上传（rel_path 已经包含 /{agent_id}/ 前缀）
        sandbox_files: list[tuple[str, bytes]] = [
            (f"/skills{rel_path}", content) for rel_path, content in files
        ]
        logger.info("正在同步 %d 个技能文件到沙盒 %s", len(sandbox_files), sandbox_id)
        responses = await backend.aupload_files(sandbox_files)

        errors = [r for r in responses if r.error]
        if errors:
            logger.warning(
                "技能文件同步失败 %d 个: %s",
                len(errors),
                [(r.path, r.error) for r in errors[:5]],
            )

        # 从 SKILL.md 中提取网络域名并应用
        skill_domains = self._extract_network_domains(files)
        if skill_domains:
            try:
                await self._apply_network_rules(backend, skill_domains)
                logger.info(
                    "已应用 %d 个网络域名规则到沙盒 %s: %s",
                    len(skill_domains),
                    sandbox_id,
                    skill_domains,
                )
            except Exception:
                logger.exception("应用网络规则到沙盒 %s 失败", sandbox_id)

        return {"_skills_synced": sandbox_id}

    async def _collect_skill_files(self, dir_path: str) -> list[tuple[str, bytes]]:
        """递归收集技能目录下的所有文件。

        Args:
            dir_path: 虚拟路径，如 ``/{agent_id}/``。

        Returns:
            ``[(相对路径, 文件内容字节)]`` 列表，相对路径形如 ``/skill-name/SKILL.md``。
        """
        result: list[tuple[str, bytes]] = []
        ls_result = await self._local_fs.als(dir_path)
        if not ls_result.entries:
            return result

        file_paths: list[str] = []
        dirs_to_walk: list[str] = []
        for entry in ls_result.entries:
            if entry.get("is_dir"):
                dirs_to_walk.append(entry["path"])
            else:
                file_paths.append(entry["path"])

        if file_paths:
            responses = await self._local_fs.adownload_files(file_paths)
            for resp in responses:
                if resp.error is None and resp.content is not None:
                    result.append((resp.path, resp.content))

        for sub_dir in dirs_to_walk:
            sub_files = await self._collect_skill_files(sub_dir)
            result.extend(sub_files)

        return result

    @staticmethod
    def _extract_network_domains(
        files: list[tuple[str, bytes]],
    ) -> list[str]:
        """从已收集的技能文件中提取 ``network-domains`` 声明。

        只解析 SKILL.md 文件的 YAML frontmatter，取并集去重。
        """
        domains: list[str] = []
        seen: set[str] = set()
        for path, content in files:
            if not path.endswith("/SKILL.md"):
                continue
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                continue
            # 匹配 YAML frontmatter
            match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
            if not match:
                continue
            try:
                fm = yaml.safe_load(match.group(1))
            except yaml.YAMLError:
                continue
            if not isinstance(fm, dict):
                continue
            raw = fm.get("network-domains")
            if not isinstance(raw, list):
                continue
            for d in raw:
                if isinstance(d, str) and d.strip() not in seen:
                    seen.add(d.strip())
                    domains.append(d.strip())
        return domains

    @staticmethod
    async def _apply_network_rules(backend: object, domains: list[str]) -> None:
        """通过 EgressAdapter 向运行中沙盒添加网络放行规则。"""
        sandbox = cast(Any, backend).sandbox
        egress_endpoint = sandbox.get_endpoint(DEFAULT_EGRESS_PORT)
        egress = EgressAdapter(
            connection_config=sandbox.connection_config,
            endpoint=egress_endpoint,
        )
        rules = [NetworkRule(action="allow", target=d) for d in domains]
        await egress.patch_rules(rules)
