"""Memory scope definitions for DeepAgents memory.

记忆按作用域分为四类，对应不同的 LangGraph Store namespace 和虚拟路径前缀，
统一在 /memories/ 下通过子路由实现多作用域隔离（遵循 DeepAgents 官方文档模式）：

- AGENT:    namespace=(assistant_id,)                    prefix=/memories/agent/    全用户共享的智能体人设
- USER:     namespace=(assistant_id, user_id)            prefix=/memories/user/     按用户隔离的偏好与摘要
- MIXTURE:  namespace=(assistant_id, user_id, "mixture") prefix=/memories/mixture/  自定义文件，按 agent×user 隔离
- ORG:      namespace=(org_id,)                          prefix=/memories/policies/ 组织级只读策略
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
    "PREFERENCES.md": MemoryScope.USER,
}

DEFAULT_ORG_ID = "default-org"


def infer_scope(filename: str) -> MemoryScope:
    """根据文件名推断默认作用域（大小写不敏感）；未匹配的文件默认归入 MIXTURE。"""
    upper = filename.upper()
    for key, scope in DEFAULT_SCOPE_BY_FILENAME.items():
        if key.upper() == upper:
            return scope
    return MemoryScope.MIXTURE


def scope_path_prefix(scope: MemoryScope) -> str:
    """返回作用域对应的虚拟路径前缀。"""
    if scope is MemoryScope.AGENT:
        return "/memories/agent/"
    if scope is MemoryScope.USER:
        return "/memories/user/"
    if scope is MemoryScope.MIXTURE:
        return "/memories/mixture/"
    if scope is MemoryScope.ORG:
        return "/memories/policies/"
    raise ValueError(f"未知作用域: {scope}")


def scope_namespace(
    scope: MemoryScope,
    *,
    agent_id: str,
    user_id: str | None,
    org_id: str | None,
) -> tuple[str, ...]:
    """返回作用域对应的 Store namespace 元组。

    USER/MIXTURE 作用域直接使用传入的 user_id，不再使用模板哨兵。
    """
    if scope is MemoryScope.AGENT:
        return (agent_id,)
    if scope is MemoryScope.USER:
        return (agent_id, user_id)  # type: ignore[arg-type]
    if scope is MemoryScope.MIXTURE:
        return (agent_id, user_id, "mixture")  # type: ignore[arg-type]
    if scope is MemoryScope.ORG:
        return (org_id or DEFAULT_ORG_ID,)
    raise ValueError(f"未知作用域: {scope}")


def build_memory_path(scope: MemoryScope, filename: str) -> str:
    """拼接作用域前缀与文件名，得到完整虚拟路径。"""
    return f"{scope_path_prefix(scope)}{filename}"
