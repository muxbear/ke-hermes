"""Integration tests for agent management API."""
import json
import uuid

import pytest

from core.security import create_token_pair

pytestmark = pytest.mark.anyio

USER_ID = f"test-{uuid.uuid4().hex[:8]}"


def _auth_headers() -> dict[str, str]:
    tokens = create_token_pair(USER_ID)
    return {"Authorization": f"Bearer {tokens.accessToken}"}


async def test_list_agents_auto_seed(client):
    """First access auto-creates a default main agent."""
    resp = await client.get("/api/agents", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 0
    assert len(data["data"]["agents"]) >= 1
    main = data["data"]["agents"][0]
    assert main["type"] == "main"


async def test_list_agents_unauthorized(client):
    resp = await client.get("/api/agents")
    assert resp.status_code == 401


async def test_create_sub_agent(client):
    """Full flow: get main agent -> create sub -> verify hierarchy."""
    resp = await client.get("/api/agents", headers=_auth_headers())
    main = resp.json()["data"]["agents"][0]

    resp = await client.post(
        "/api/agents",
        json={"name": "测试子代理", "parent_id": main["id"]},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    sub = resp.json()["data"]
    assert sub["type"] == "sub"
    assert sub["parent_id"] == main["id"]

    resp = await client.get("/api/agents", headers=_auth_headers())
    main_updated = resp.json()["data"]["agents"][0]
    assert sub["id"] in main_updated["sub_agents"]


async def test_get_agent_not_found(client):
    resp = await client.get(
        "/api/agents/nonexistent-id", headers=_auth_headers()
    )
    # ApiResponse wraps errors — code field holds the error code
    assert resp.json()["code"] == 404


async def test_create_agent_empty_name(client):
    resp = await client.post(
        "/api/agents", json={"name": ""}, headers=_auth_headers()
    )
    assert resp.status_code == 422


async def test_toggle_status(client):
    resp = await client.get("/api/agents", headers=_auth_headers())
    agent = resp.json()["data"]["agents"][0]
    agent_id = agent["id"]
    initial_status = agent["status"]

    # Toggle once
    resp = await client.patch(
        f"/api/agents/{agent_id}/status", headers=_auth_headers()
    )
    assert resp.status_code == 200
    toggled = resp.json()["data"]["status"]
    assert toggled != initial_status

    # Toggle back
    resp = await client.patch(
        f"/api/agents/{agent_id}/status", headers=_auth_headers()
    )
    assert resp.json()["data"]["status"] == initial_status


async def test_clone_agent(client):
    resp = await client.get("/api/agents", headers=_auth_headers())
    agent_id = resp.json()["data"]["agents"][0]["id"]

    resp = await client.post(
        f"/api/agents/{agent_id}/clone", headers=_auth_headers()
    )
    assert resp.status_code == 200
    cloned = resp.json()["data"]
    assert cloned["status"] == "inactive"


async def test_add_and_remove_config(client):
    resp = await client.get("/api/agents", headers=_auth_headers())
    agent_id = resp.json()["data"]["agents"][0]["id"]

    # Add tool
    resp = await client.post(
        f"/api/agents/{agent_id}/config",
        json={"type": "tool", "value": "web_search"},
        headers=_auth_headers(),
    )
    assert resp.status_code == 200
    assert "web_search" in resp.json()["data"]["tools"]

    # Remove tool — httpx DELETE doesn't accept `json`, use `content`
    resp = await client.request(
        "DELETE",
        f"/api/agents/{agent_id}/config",
        content=json.dumps({"type": "tool", "value": "web_search"}),
        headers={**_auth_headers(), "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    assert "web_search" not in resp.json()["data"]["tools"]


async def test_delete_undeletable_fails(client):
    resp = await client.get("/api/agents", headers=_auth_headers())
    # Find the auto-seeded undeletable agent
    main = [a for a in resp.json()["data"]["agents"] if a["type"] == "main"][0]
    resp = await client.delete(
        f"/api/agents/{main['id']}", headers=_auth_headers()
    )
    # ApiResponse wraps errors — code field holds the error code
    assert resp.json()["code"] == 403


async def test_full_crud_lifecycle(client):
    """Complete lifecycle: create sub -> toggle -> clone -> delete."""
    headers = _auth_headers()

    list_resp = await client.get("/api/agents", headers=headers)
    main = list_resp.json()["data"]["agents"][0]

    # 1. Create sub-agent
    create_resp = await client.post(
        "/api/agents",
        json={"name": "完整流程测试", "parent_id": main["id"]},
        headers=headers,
    )
    assert create_resp.status_code == 200
    sub = create_resp.json()["data"]

    # 2. Get agent
    get_resp = await client.get(f"/api/agents/{sub['id']}", headers=headers)
    assert get_resp.status_code == 200

    # 3. Toggle status (starts inactive, goes to active)
    toggle_resp = await client.patch(
        f"/api/agents/{sub['id']}/status", headers=headers
    )
    assert toggle_resp.json()["data"]["status"] == "active"

    # 4. Clone
    clone_resp = await client.post(
        f"/api/agents/{sub['id']}/clone", headers=headers
    )
    assert clone_resp.status_code == 200

    # 5. Delete clone
    del_resp = await client.delete(
        f"/api/agents/{clone_resp.json()['data']['id']}", headers=headers
    )
    assert del_resp.status_code == 200

    # 6. Delete sub
    del_resp = await client.delete(
        f"/api/agents/{sub['id']}", headers=headers
    )
    assert del_resp.status_code == 200
