"""Tests for EventBus."""

import pytest
from core.event_bus import EventBus, Events


class TestEventBus:
    def setup_method(self):
        EventBus.clear()

    def teardown_method(self):
        EventBus.clear()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self):
        """订阅后发布事件应调用所有处理器。"""
        received: list[dict] = []

        async def handler(**payload):
            received.append(payload)

        EventBus.subscribe("test.event", handler)
        await EventBus.publish("test.event", key="value", num=42)

        assert len(received) == 1
        assert received[0] == {"key": "value", "num": 42}

    @pytest.mark.asyncio
    async def test_multiple_handlers(self):
        """同一事件类型可注册多个处理器。"""
        calls = []

        async def h1(**kwargs):
            calls.append("h1")

        async def h2(**kwargs):
            calls.append("h2")

        EventBus.subscribe("multi", h1)
        EventBus.subscribe("multi", h2)
        await EventBus.publish("multi")

        assert "h1" in calls
        assert "h2" in calls

    @pytest.mark.asyncio
    async def test_no_handlers_silent(self):
        """发布无订阅者的事件不应出错。"""
        await EventBus.publish("unsubscribed.event")

    @pytest.mark.asyncio
    async def test_unsubscribe(self):
        """取消订阅后不再接收事件。"""
        calls = []

        async def handler(**kwargs):
            calls.append(1)

        EventBus.subscribe("test", handler)
        EventBus.unsubscribe("test", handler)
        await EventBus.publish("test")

        assert len(calls) == 0

    @pytest.mark.asyncio
    async def test_handler_error_does_not_block_others(self):
        """一个处理器异常不应阻止其他处理器。"""
        calls = []

        async def failing(**kwargs):
            raise RuntimeError("boom")

        async def ok_handler(**kwargs):
            calls.append("ok")

        EventBus.subscribe("test", failing)
        EventBus.subscribe("test", ok_handler)
        await EventBus.publish("test")

        assert "ok" in calls

    def test_events_constants(self):
        """验证预定义事件常量。"""
        assert Events.AGENT_CREATED == "agent.created"
        assert Events.DOCUMENT_INDEXED == "document.indexed"
        assert Events.KNOWLEDGE_BASE_DELETED == "knowledge_base.deleted"
