"""Memory scope definitions for DeepAgents memory.

记忆按作用域分为四类，对应不同的 LangGraph Store namespace 和虚拟路径前缀：

- AGENT:    namespace=(agent_id,)              prefix=/memories/agent/    全用户共享的智能体人设
- USER:     namespace=(agent_id, user_id)      prefix=/memories/user/     按用户隔离的偏好与摘要
- MIXTURE:  namespace=(agent_id, user_id)      prefix=/memories/mixture/  自定义文件，按 agent×user 隔离
- ORG:      namespace=(org_id,)                prefix=/policies/          组织级只读策略
"""
from __future__ import annotations

from enum import Enum


class MemoryScope(str, Enum):
    """记忆作用域枚举。"""

    AGENT = "agent"
    USER = "user"
    MIXTURE = "mixture"
    ORG = "org"


DEFAULT_SCOPE_BY_FILENAME: dict[str, MemoryScope] = {
    "AGENTS.md": MemoryScope.AGENT,
    "SOUL.md": MemoryScope.AGENT,
    "IDENTITY.md": MemoryScope.AGENT,
    "TOOLS.md": MemoryScope.AGENT,
    "HEARTBEAT.md": MemoryScope.AGENT,
    "USER.md": MemoryScope.USER,
    "MEMORY.md": MemoryScope.USER,
}

DEFAULT_ORG_ID = "default-org"
TEMPLATE_USER_ID = "__template__"


def infer_scope(filename: str) -> MemoryScope:
    """根据文件名推断默认作用域；未匹配的文件默认归入 MIXTURE。"""
    return DEFAULT_SCOPE_BY_FILENAME.get(filename, MemoryScope.MIXTURE)


def scope_path_prefix(scope: MemoryScope) -> str:
    """返回作用域对应的虚拟路径前缀。"""
    if scope is MemoryScope.AGENT:
        return "/memories/agent/"
    if scope is MemoryScope.USER:
        return "/memories/user/"
    if scope is MemoryScope.MIXTURE:
        return "/memories/mixture/"
    if scope is MemoryScope.ORG:
        return "/policies/"
    raise ValueError(f"未知作用域: {scope}")


def scope_namespace(
    scope: MemoryScope,
    *,
    agent_id: str,
    user_id: str | None,
    org_id: str | None,
) -> tuple[str, ...]:
    """返回作用域对应的 Store namespace 元组。

    对于 USER/MIXTURE 作用域，user_id 为空时使用 TEMPLATE_USER_ID，
    以便管理员保存的模板内容可作为种子被用户首次对话时读取。
    """
    if scope is MemoryScope.AGENT:
        return (agent_id,)
    if scope is MemoryScope.USER or scope is MemoryScope.MIXTURE:
        return (agent_id, user_id or TEMPLATE_USER_ID)
    if scope is MemoryScope.ORG:
        return (org_id or DEFAULT_ORG_ID,)
    raise ValueError(f"未知作用域: {scope}")


def build_memory_path(scope: MemoryScope, filename: str) -> str:
    """拼接作用域前缀与文件名，得到完整虚拟路径。"""
    return f"{scope_path_prefix(scope)}{filename}"
