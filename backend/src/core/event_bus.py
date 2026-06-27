"""轻量事件总线——发布/订阅模式解耦跨模块通知。

使用方式:
    await EventBus.publish("document.indexed", doc_id="xxx", kb_id="yyy")
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Awaitable[None]]


class EventBus:
    """应用级事件总线。

    订阅:
        EventBus.subscribe("agent.created", on_agent_created)

    发布:
        await EventBus.publish("agent.created", agent_id="xxx", user_id="yyy")
    """

    _subscriptions: dict[str, list[EventHandler]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: str, handler: EventHandler) -> None:
        """订阅事件。"""
        cls._subscriptions[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: str, handler: EventHandler) -> None:
        """取消订阅。"""
        try:
            cls._subscriptions[event_type].remove(handler)
        except ValueError:
            pass

    @classmethod
    async def publish(cls, event_type: str, **payload: object) -> None:
        """异步发布事件给所有订阅者。

        订阅者的异常被捕获并记录，不会中断其他订阅者。
        """
        handlers = cls._subscriptions.get(event_type, [])
        if not handlers:
            return
        results = await asyncio.gather(
            *[handler(**payload) for handler in handlers],
            return_exceptions=True,
        )
        for handler, result in zip(handlers, results):
            if isinstance(result, Exception):
                logger.error(
                    "事件处理器 %s 在事件 %s 中失败: %s",
                    handler.__name__,
                    event_type,
                    result,
                )

    @classmethod
    def clear(cls) -> None:
        """清除所有订阅（测试用）。"""
        cls._subscriptions.clear()


class Events:
    """预定义事件类型常量。"""

    AGENT_CREATED = "agent.created"
    AGENT_DELETED = "agent.deleted"
    AGENT_STATUS_CHANGED = "agent.status_changed"

    DOCUMENT_INDEXED = "document.indexed"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_INDEX_FAILED = "document.index_failed"

    KNOWLEDGE_BASE_CREATED = "knowledge_base.created"
    KNOWLEDGE_BASE_DELETED = "knowledge_base.deleted"

    USER_REGISTERED = "user.registered"
    PROVIDER_API_KEY_UPDATED = "provider.api_key_updated"
