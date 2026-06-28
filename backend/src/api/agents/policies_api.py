"""组织级只读策略 (policies) 管理 API。

组织级记忆存储在 LangGraph Store namespace=(org_id,) 下，前缀 /memories/policies/。
v1 提供：列出 + 读取 + 写入（管理员）。Files 标签页仅展示，不通过此接口编辑。
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import get_store
from agent.memory.file_data import create_agent_file_data, file_value_to_agent_file_content
from agent.memory.scopes import DEFAULT_ORG_ID, MemoryScope, infer_scope
from api.agents.schemas import AgentFileContent
from api.deps import get_db
from core.decorators import handle_errors
from core.response import ApiResponse, ok
from db.models.agent import Agent

logger = logging.getLogger(__name__)

router = APIRouter(tags=["policies"])


class PolicyWriteRequest(BaseModel):
    """写入组织级策略文件请求体。"""

    content: str = ""
    description: str = ""
    org_id: str = Field(default=DEFAULT_ORG_ID, description="组织 ID")


@router.get(
    "/{agent_id}/policies",
    response_model=ApiResponse[list[AgentFileContent]],
)
@handle_errors
async def list_policies(
    agent_id: str,
    org_id: str = Query(DEFAULT_ORG_ID, description="组织 ID"),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[list[AgentFileContent]]:
    """列出指定组织下的所有只读策略文件（从 Store 读取）。"""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    files = agent.files if isinstance(agent.files, list) else []
    result: list[AgentFileContent] = []

    try:
        store = get_store()
    except RuntimeError:
        return ok(result)

    namespace: tuple[str, ...] = (org_id,)
    for filename in files:
        scope = infer_scope(filename)
        if scope is not MemoryScope.ORG:
            continue
        try:
            item = await store.aget(namespace, f"/{filename}")
            if item is not None:
                d = file_value_to_agent_file_content(item.value, filename, default_scope=MemoryScope.ORG)
                result.append(AgentFileContent(**d))
        except Exception:
            pass

    return ok(result)


@router.put(
    "/{agent_id}/policies/{filename:path}",
    response_model=ApiResponse[AgentFileContent],
)
@handle_errors
async def write_policy(
    agent_id: str,
    filename: str,
    req: PolicyWriteRequest,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AgentFileContent]:
    """写入（新建/更新）组织级策略文件到 Store。"""
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    namespace: tuple[str, ...] = (req.org_id,)
    value = create_agent_file_data(
        content=req.content,
        description=req.description,
        scope=MemoryScope.ORG,
        read_only=True,
        org_id=req.org_id,
    )

    try:
        store = get_store()
        await store.aput(namespace, f"/{filename}", value)
    except RuntimeError:
        logger.warning("Store 未初始化，策略文件 %s 未持久化", filename)
    except Exception:
        logger.exception("写入策略文件 %s 到 Store 失败", filename)

    return ok(AgentFileContent(
        filename=filename,
        content=req.content,
        description=req.description,
        scope=MemoryScope.ORG,
        read_only=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    ))
