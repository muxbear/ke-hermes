"""Store 文件写入/删除辅助函数。

Admin 编辑文件后通过此模块将内容写入 LangGraph Store（直接写入，无 DB 中间层）。
USER/MIXTURE 作用域的文件以 user_id="__template__" 写入模板命名空间。
"""
from __future__ import annotations

import logging
from typing import Any

from agent.memory.scopes import (
    TEMPLATE_USER_ID,
    MemoryScope,
    scope_namespace,
)
from agent.memory.file_data import create_agent_file_data

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
    namespace = scope_namespace(
        scope, agent_id=agent_id, user_id=user_id, org_id=org_id
    )
    value = create_agent_file_data(content=content, scope=scope)
    await store.aput(namespace, f"/{filename}", value)
    logger.debug(
        "已写入文件 %s (scope=%s) 到 Store namespace=%s",
        filename, scope.value, namespace,
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
    try:
        await store.adelete(namespace, f"/{filename}")
    except Exception:
        logger.warning("从 Store 删除 %s 失败（可能不存在）", filename, exc_info=True)


__all__ = [
    "delete_agent_file_from_store",
    "sync_agent_file_to_store",
]
