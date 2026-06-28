"""Store 文件数据辅助函数 — 创建和提取兼容 deepagents FileData 的记忆文件。

deepagents 使用的 FileData 格式为 ``{"content": str, "encoding": str, ...}``。
本模块在此基础之上扩展了元数据字段（description / scope / read_only / org_id），
并存放在同一个 dict 中。deepagents 框架只读取 content 和 encoding，其他键被容忍。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.memory.scopes import MemoryScope, infer_scope


def create_agent_file_data(
    content: str,
    *,
    description: str = "",
    scope: MemoryScope | str = MemoryScope.AGENT,
    read_only: bool = False,
    org_id: str | None = None,
) -> dict[str, Any]:
    """创建兼容 deepagents FileData 且含元数据的文件 dict。

    Args:
        content: 文件 Markdown / 文本内容。
        description: 文件描述（管理员可见的注释）。
        scope: 记忆作用域。
        read_only: 是否只读（组织级策略文件为 True）。
        org_id: 组织 ID（仅 ORG 作用域使用）。

    Returns:
        包含 content / encoding / description / scope / read_only / org_id
        及时间戳的 dict，可直接作为 ``store.aput()`` 的 value。
    """
    now = datetime.now(timezone.utc).isoformat()
    return {
        "content": content,
        "encoding": "utf-8",
        "description": description,
        "scope": scope if isinstance(scope, str) else scope.value,
        "read_only": read_only,
        "org_id": org_id,
        "created_at": now,
        "modified_at": now,
    }


def file_value_to_content(value: Any, fallback: str = "") -> str:
    """从 Store value 中提取 content 字段。

    Args:
        value: ``store.aget()`` 返回的 ``Item.value``（dict 或 兼容对象）。
        fallback: value 为 None 或无 content 键时返回的默认值。

    Returns:
        文件文本内容。
    """
    if value is None:
        return fallback
    if isinstance(value, dict):
        return str(value.get("content", fallback))
    return str(getattr(value, "content", fallback))


def file_value_to_metadata(
    value: Any,
    *,
    default_scope: MemoryScope | None = None,
    default_read_only: bool = False,
) -> dict[str, Any]:
    """从 Store value 中提取元数据，缺失键使用默认值。

    Args:
        value: Store Item value（dict 或 兼容对象）。
        default_scope: scope 缺失时的默认作用域。
        default_read_only: read_only 缺失时的默认值。

    Returns:
        ``{"description": str, "scope": str, "read_only": bool, "org_id": str|None,
        "created_at": str, "modified_at": str}``。
    """
    if value is None:
        return _default_metadata(default_scope, default_read_only)

    if isinstance(value, dict):
        return {
            "description": str(value.get("description", "")),
            "scope": str(value.get("scope", default_scope.value if default_scope else "agent")),
            "read_only": bool(value.get("read_only", default_read_only)),
            "org_id": value.get("org_id"),
            "created_at": str(value.get("created_at", "")),
            "modified_at": str(value.get("modified_at", "")),
        }

    return {
        "description": str(getattr(value, "description", "")),
        "scope": str(getattr(value, "scope", default_scope.value if default_scope else "agent")),
        "read_only": bool(getattr(value, "read_only", default_read_only)),
        "org_id": getattr(value, "org_id", None),
        "created_at": str(getattr(value, "created_at", "")),
        "modified_at": str(getattr(value, "modified_at", "")),
    }


def _to_memory_scope(value: Any, fallback: MemoryScope) -> MemoryScope:
    """将任意值安全转换为 MemoryScope，失败时返回 fallback。"""
    if isinstance(value, MemoryScope):
        return value
    try:
        return MemoryScope(str(value))
    except (ValueError, TypeError):
        return fallback


def _default_metadata(
    default_scope: MemoryScope | None, default_read_only: bool
) -> dict[str, Any]:
    return {
        "description": "",
        "scope": default_scope.value if default_scope else "agent",
        "read_only": default_read_only,
        "org_id": None,
        "created_at": "",
        "modified_at": "",
    }


def file_value_to_agent_file_content(
    value: Any,
    filename: str,
    *,
    default_scope: MemoryScope | None = None,
) -> dict[str, Any]:
    """将 Store value 转为 AgentFileContent 兼容的 dict。

    Args:
        value: Store Item value。
        filename: 文件名。
        default_scope: scope 缺失时的默认作用域。

    Returns:
        包含 ``filename`` / ``content`` / ``description`` / ``scope`` /
        ``read_only`` / ``created_at`` / ``updated_at`` 的 dict。
    """
    meta = file_value_to_metadata(value, default_scope=default_scope)
    content = file_value_to_content(value)
    scope = _to_memory_scope(meta["scope"], infer_scope(filename))
    return {
        "filename": filename,
        "content": content,
        "description": meta["description"],
        "scope": scope,
        "read_only": meta["read_only"],
        "created_at": meta["created_at"],
        "updated_at": meta["modified_at"],
    }


__all__ = [
    "create_agent_file_data",
    "file_value_to_agent_file_content",
    "file_value_to_content",
    "file_value_to_metadata",
]
