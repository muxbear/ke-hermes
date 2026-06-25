"""组织级只读策略 (policies) 管理 API。

组织级记忆存储在 LangGraph Store namespace=(org_id,) 下，前缀 /policies/。
v1 提供：列出 + 读取 + 写入（管理员）。Files 标签页仅展示，不通过此接口编辑。
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import get_store
from agent.memory.memory_sync import sync_agent_file_to_store
from agent.memory.scopes import DEFAULT_ORG_ID, MemoryScope
from api.agents.schemas import AgentFileContent
from api.deps import get_db
from core.decorators import handle_errors
from core.response import ApiResponse, ok
from db.models.agent import Agent
from db.models.agent_file import AgentFile

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
    """列出指定组织下的所有只读策略文件。"""  # noqa: D415
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    file_stmt = select(AgentFile).where(
        AgentFile.scope == MemoryScope.ORG.value,
        AgentFile.org_id == org_id,
    )
    rows = (await db.execute(file_stmt)).scalars().all()
    result = [
        AgentFileContent(
            filename=row.filename,
            content=row.content or "",
            description=row.description or "",
            scope=MemoryScope.ORG,
            read_only=True,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]
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
    """写入（新建/更新）组织级策略文件。"""  # noqa: D415
    stmt = select(Agent).where(Agent.id == agent_id)
    agent = (await db.execute(stmt)).scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    file_stmt = select(AgentFile).where(
        AgentFile.scope == MemoryScope.ORG.value,
        AgentFile.org_id == req.org_id,
        AgentFile.filename == filename,
    )
    row = (await db.execute(file_stmt)).scalar_one_or_none()
    if row is None:
        row = AgentFile(
            agent_id=agent_id,
            filename=filename,
            content=req.content,
            description=req.description,
            scope=MemoryScope.ORG.value,
            read_only=True,
            org_id=req.org_id,
        )
        db.add(row)
    else:
        row.content = req.content
        row.description = req.description

    await db.flush()

    # 同步到 Store
    try:
        store: Any = get_store()
        await sync_agent_file_to_store(
            store,
            agent_id=agent_id,
            user_id=None,
            org_id=req.org_id,
            filename=filename,
            content=req.content,
            scope=MemoryScope.ORG,
        )
    except Exception:
        logger.exception("同步策略文件 %s 到 Store 失败", filename)

    return ok(AgentFileContent(
        filename=row.filename,
        content=row.content or "",
        description=row.description or "",
        scope=MemoryScope.ORG,
        read_only=True,
        created_at=row.created_at,
        updated_at=row.updated_at,
    ))
