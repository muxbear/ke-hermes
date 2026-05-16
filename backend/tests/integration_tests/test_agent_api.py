import os

import pytest

pytestmark = pytest.mark.anyio

HAS_REAL_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "").startswith("sk-") and os.environ.get("DEEPSEEK_API_KEY") != "sk-test"


@pytest.mark.skipif(not HAS_REAL_API_KEY, reason="需要真实的 DEEPSEEK_API_KEY 环境变量")
async def test_chat(client):
    resp = await client.post("/api/chat", json={"message": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert isinstance(data["response"], str)


async def test_chat_validation_empty_message(client):
    resp = await client.post("/api/chat", json={"message": ""})
    assert resp.status_code == 422


async def test_chat_validation_missing_field(client):
    resp = await client.post("/api/chat", json={})
    assert resp.status_code == 422


@pytest.mark.skipif(not HAS_REAL_API_KEY, reason="需要真实的 DEEPSEEK_API_KEY 环境变量")
async def test_chat_stream(client):
    resp = await client.post("/api/chat/stream", json={"message": "hello"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


async def test_chat_stream_validation(client):
    resp = await client.post("/api/chat/stream", json={"message": ""})
    assert resp.status_code == 422