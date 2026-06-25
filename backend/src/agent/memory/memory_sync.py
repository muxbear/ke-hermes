"""同步 AgentFile DB 内容到 LangGraph Store。

Files 标签页（管理员视图）编辑的内容是「模板/种子」：
- AGENT/ORG 作用域：DB 内容即运行时内容，全用户共享
- USER/MIXTURE 作用域：DB 内容作为模板，user_id="__template__" 写入 Store；
  用户首次对话时由 Agent 自行 edit_file 创建各自实例

运行时 Agent 通过 memory=[...] 路径从 Store 读取，不再直接读 DB（关闭 G2）。
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.memory.scopes import (
    TEMPLATE_USER_ID,
    MemoryScope,
    build_memory_path,
    infer_scope,
    scope_namespace,
)
from db.models.agent_file import AgentFile

logger = logging.getLogger(__name__)


async def sync_agent_file_to_store(
    store: Any,
    *,
    agent_id: str,
    user_id: str | None,
    org_id: str | None,
    filename: str,
    content: str,
    scope: MemoryScope,
) -> None:
    """将单个文件内容写入 LangGraph Store 对应 namespace。

    Args:
        store: LangGraph Store 实例（InMemoryStore 或 AsyncPostgresStore）。
        agent_id: 智能体 ID。
        user_id: 用户 ID；USER/MIXTURE 作用域为空时使用模板哨兵。
        org_id: 组织 ID；ORG 作用域为空时使用默认值。
        filename: 文件名（不含路径前缀）。
        content: 文件 Markdown/文本内容。
        scope: 记忆作用域。
    """
    from deepagents.backends.utils import create_file_data

    namespace = scope_namespace(
        scope, agent_id=agent_id, user_id=user_id, org_id=org_id
    )
    path = build_memory_path(scope, filename)
    await store.aput(namespace, path, create_file_data(content))
    logger.debug(
        "已同步文件 %s (scope=%s) 到 Store namespace=%s", path, scope.value, namespace
    )


async def delete_agent_file_from_store(
    store: Any,
    *,
    agent_id: str,
    user_id: str | None,
    org_id: str | None,
    filename: str,
    scope: MemoryScope,
) -> None:
    """从 Store 中删除指定文件。"""
    namespace = scope_namespace(
        scope, agent_id=agent_id, user_id=user_id, org_id=org_id
    )
    path = build_memory_path(scope, filename)
    try:
        await store.adelete(namespace, path)
    except Exception:
        logger.warning("从 Store 删除 %s 失败（可能不存在）", path, exc_info=True)


async def bootstrap_agent_memory(store: Any, db: AsyncSession) -> None:
    """应用启动时将 AgentFile 表中所有文件种子化到 Store。

    - AGENT/ORG 作用域：直接写入对应 namespace
    - USER/MIXTURE 作用域：写入 (agent_id, "__template__") 命名空间作为模板
    """
    stmt = select(AgentFile)
    rows = (await db.execute(stmt)).scalars().all()
    if not rows:
        logger.info("AgentFile 表为空，跳过记忆 bootstrap")
        return

    count = 0
    for row in rows:
        scope = MemoryScope(row.scope) if row.scope else infer_scope(row.filename)
        await sync_agent_file_to_store(
            store,
            agent_id=row.agent_id,
            user_id=TEMPLATE_USER_ID,
            org_id=row.org_id,
            filename=row.filename,
            content=row.content or "",
            scope=scope,
        )
        count += 1
    logger.info("记忆 bootstrap 完成，共同步 %d 个文件到 Store", count)


__all__ = [
    "TEMPLATE_USER_ID",
    "bootstrap_agent_memory",
    "delete_agent_file_from_store",
    "sync_agent_file_to_store",
]
